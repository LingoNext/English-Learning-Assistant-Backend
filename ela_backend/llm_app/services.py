import base64
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from django.conf import settings
from huggingface_hub import InferenceClient
from io import BytesIO
from PIL import Image, ImageOps


@dataclass
class NovitaQwenClient:
    api_key: str
    api_url: str
    model_id: str
    timeout: int = 120
    client: Optional[InferenceClient] = field(default=None, init=False, repr=False)

    def analyze_image(self, image_bytes: bytes) -> Dict[str, Any]:
        data_uri = self.to_data_uri(image_bytes)
        prompt, messages = self.build_messages(data_uri)
        payload = {
            "messages": messages,
            "max_tokens": 700,
            "temperature": 0.7,
        }
        response = self.post(payload)
        response_text = self.extract_text(response)
        parsed = self.parse_structured_payload(response_text)

        return {
            "prompt": prompt,
            "messages": messages,
            "raw_response": response,
            "parsed": parsed,
        }

    def analyze_text(self, messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        payload = {
            "messages": messages,
            "max_tokens": 700,
            "temperature": 0.7,
        }
        response = self.post(payload)
        response_text = self.extract_text(response)
        parsed = self.parse_structured_payload(response_text)
        return {
            "messages": messages,
            "raw_response": response,
            "raw_text": response_text,
            "parsed": parsed,
        }

    def post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        client = self.get_client()
        try:
            completion = client.chat.completions.create(
                model=self.model_id,
                messages=payload["messages"],
                max_tokens=payload.get("max_tokens"),
                temperature=payload.get("temperature"),
            )
        except Exception as exc:
            raise Exception(
                f"HuggingFace inference failed for model '{self.model_id}' at '{self.api_url}': {exc}"
            ) from exc

        serialized = self.serialize_completion(completion)
        if not isinstance(serialized, dict):
            raise Exception("Unexpected response format from HuggingFace inference.")
        return serialized

    def get_client(self) -> InferenceClient:
        if self.client is None:
            client_kwargs: Dict[str, Any] = {"api_key": self.api_key, "timeout": self.timeout}
            if self.api_url:
                client_kwargs["base_url"] = self.api_url
            try:
                self.client = InferenceClient(**client_kwargs)
            except TypeError:
                client_kwargs.pop("base_url", None)
                self.client = InferenceClient(**client_kwargs)
        return self.client

    def to_data_uri(self, image_bytes: bytes) -> str:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"

    def build_messages(self, data_uri: str) -> tuple[str, List[Dict[str, Any]]]:
        prompt = (
            "AR tutor. JSON only. Find 2-3 objects:\n"
            "{\"vocabulary\":[{\"word_en\":\"\",\"word_zh\":\"Traditional Chinese\",\"pos\":\"noun\"}],\"sentences\":[{\"english\":\"\",\"chinese\":\"Traditional Chinese\"}]}\n"
            "Rules: Each chinese translation MUST be in traditional chinese, vocabulary=2-3 items, sentences=same count, use each word once"
        )
        messages = [
            {"role": "system", "content": prompt},
            {
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": data_uri}}
                ],
            },
        ]

        return prompt, messages

    def extract_text(self, response: Dict[str, Any]) -> str:
        if "generated_text" in response:
            return response["generated_text"]
        if "choices" in response and response["choices"]:
            choice = response["choices"][0]
            message = choice.get("message") or {}
            if isinstance(message, dict) and "content" in message:
                return message["content"]
        if isinstance(response, dict):
            # Some providers return {"output_text": "..."} etc.
            for key in ("output_text", "text", "data"):
                candidate = response.get(key)
                if isinstance(candidate, str):
                    return candidate
        raise Exception("Unable to locate generated text in Novita response.")

    def serialize_completion(self, completion: Any) -> Any:
        if isinstance(completion, dict):
            return completion

        for attr in ("model_dump", "to_dict", "dict"):
            method = getattr(completion, attr, None)
            if callable(method):
                try:
                    candidate = method()
                except TypeError:
                    candidate = method(exclude_none=True)
                if isinstance(candidate, dict):
                    return candidate

        completion_dict = getattr(completion, "__dict__", None)
        if isinstance(completion_dict, dict):
            return completion_dict
        return completion

    def parse_structured_payload(self, text: str) -> Dict[str, Any]:
        cleaned = text.strip()
        candidate = cleaned
        if "```" in cleaned:
            candidate = "".join(line for line in cleaned.splitlines() if not line.strip().startswith("```"))

        json_match = re.search(r"({.*})", candidate, flags=re.DOTALL)
        if json_match:
            candidate = json_match.group(1)

        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            pass
        return {"error": "Failed to parse structured payload"}

    def build_chat_messages(
            self,
            conversation: List[Dict[str, str]],
            analysis_enabled: bool,
    ) -> List[Dict[str, Any]]:
        # Keep the last few messages and summarize the rest
        recent_messages = conversation[-4:]  # Keep last 4 messages for context
        older_messages = conversation[:-4]

        if len(conversation) > 6 and older_messages:
            summary = self._summarize_conversation(older_messages)
            # Create summarized conversation
            conversation = [
                               {"role": "assistant", "content": f"Previous conversation summary: {summary}"}
                           ] + recent_messages

        if analysis_enabled:

            prompt = (
                "English tutor. JSON only.\n"
                "Format:\n"
                "{\n"
                "  \"reply\": \"natural conversational response\",\n"
                "  \"title\": \"A brief title showing the content of the conversation\",\n"
                "  \"user_grammar\": {\n"
                "    \"is_correct\": bool or null,\n"
                "    \"corrected_text\": \"string or null\",\n"
                "    \"errors\": [\"list\"],\n"
                "    \"explanation\": \"Traditional Chinese\"\n"
                "  },\n"
                "  \"grammar_structure\": {\n"
                "    \"type\": \"structure type or null\",\n"
                "    \"description\": \"brief desc or null\",\n"
                "    \"example\": \"optional or null\"\n"
                "  }\n"
                "}\n"
                "Rules:\n"
                "1. If the user input is NOT a English sentence:\n"
                "   - set \"is_correct\" to null\n"
                "   - set \"corrected_text\" to null\n"
                "   - set \"errors\" to []\n"
                "   - set \"explanation\" to \"非英文句子，不進行文法分析。\"\n"
                "   - set \"grammar_structure\" to null\n"
                "\n"
                "2. If the user input is an English sentence:\n"
                "   - perform grammar analysis normally.\n"
                "\n"
                "3. reply MUST:\n"
                "   - be a natural conversational response\n"
                "   - continue the conversation\n"
                "   - NOT repeat corrected_text\n"
                "   - NOT restate or paraphrase corrected_text\n"
                "   - NOT contain the full corrected sentence\n"
                "\n"
                "4. corrected_text is ONLY for grammar correction display.\n"
                "\n"
                "5. All Chinese text MUST be in Traditional Chinese.\n"
                "\n"
                "6. Output JSON only. No Markdown. No code block. No extra text.\n"
            )
        else:
            prompt = (
                "English tutor. JSON only:\n"
                "{\"reply\": \"Natural response, don't repeat user input\",\n"
                "  \"title\": \"A brief title showing the content of the conversation\",\n"
                "}\n"
                "Rules:\n"
                "1. 5 sentences max."
                "2. If user contains English, reply in English. Otherwise, reply in Chinese."
                "3. All Chinese text MUST be in Traditional Chinese."
                "4. Output JSON only. No Markdown. No code block. No extra text.\n"
            )
        messages: List[Dict[str, Any]] = [{"role": "system", "content": prompt}]
        messages.extend(conversation)
        return messages

    def _summarize_conversation(self, messages: List[Dict[str, str]]) -> str:
        """Summarize a conversation to reduce token usage"""
        if not messages:
            return ""

        # Build prompt for summarization
        conversation_text = ""
        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            conversation_text += f"{role}: {content}\n"

        summary_prompt = [
            {
                "role": "system",
                "content": "Summarize in 2-3 sentences. Focus on main topics and learning points."
            },
            {
                "role": "user",
                "content": f"Summarize:\n{conversation_text}"
            }
        ]

        try:
            payload = {
                "messages": summary_prompt,
                "max_tokens": 150,
                "temperature": 0.3,
            }
            response = self.post(payload)
            summary = self.extract_text(response)
            return summary.strip()
        except Exception:
            # Fallback: simple truncation if summarization fails
            return "Previous conversation about English learning topics."

    def build_vocab_messages(self, word: str) -> List[Dict[str, Any]]:
        prompt = """English tutor. Respond in JSON ONLY.
        Format:
        {
          "word": "",
          "ipa": "",
          "pos": "",
          "meaning_en": "", // MUST be in English only
          "meaning_zh": "", // MUST be in Traditional Chinese
          "example_en": "", // MUST be in English only
          "example_zh": "", // MUST be in Traditional Chinese
          "error": ""
        }
        Rules:
        1. DO NOT put any Chinese in meaning_en or example_en.
        2. All Chinese translations MUST be in Traditional Chinese.
        3. Always return valid JSON without extra text.
        4. Analyze the word in depth, including its usage, connotations, and any interesting linguistic features. The more detailed the analysis, the better."""
        user_instruction = f"Analyze: {word}"
        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_instruction},
        ]


def get_novita_client() -> NovitaQwenClient:
    """Factory that pulls configuration from Django settings."""
    if not settings.NOVITA_API_KEY:
        raise Exception("NOVITA_API_KEY is not configured.")
    return NovitaQwenClient(
        api_key=settings.NOVITA_API_KEY,
        api_url=settings.NOVITA_API_URL,
        model_id=settings.NOVITA_MODEL_ID,
        timeout=settings.NOVITA_REQUEST_TIMEOUT,
    )


class ImageCompressor:
    """"限制圖片大小的工具，確保上傳的圖片不會超過指定的檔案大小和像素數"""

    def compress_image_file(file_obj, target_width, max_bytes=2 * 1024 * 1024, max_pixels=2_000_000) -> bytes:
        file_obj.seek(0)
        img_bytes = file_obj.read()

        # 已經夠小就直接回傳
        if len(img_bytes) <= max_bytes:
            return img_bytes

        img = Image.open(BytesIO(img_bytes))
        img = ImageOps.exif_transpose(img)

        # 限制最大像素數
        pixels = img.width * img.height
        if pixels > max_pixels:
            scale = (max_pixels / pixels) ** 0.5
            img = img.resize(
                (int(img.width * scale), int(img.height * scale)),
                Image.LANCZOS
            )

        # 固定寬度（若指定）
        if target_width and img.width > target_width:
            ratio = target_width / img.width
            img = img.resize(
                (target_width, int(img.height * ratio)),
                Image.LANCZOS
            )

        # 處理 alpha
        if img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg
        else:
            img = img.convert("RGB")

        out = BytesIO()
        resize_steps = [1.0, 0.9, 0.8, 0.7, 0.6]

        for step in resize_steps:
            if step != 1.0:
                img = img.resize(
                    (int(img.width * step), int(img.height * step)),
                    Image.LANCZOS
                )

            for quality in range(90, 25, -10):
                out.seek(0)
                out.truncate(0)
                img.save(out, "JPEG", quality=quality, optimize=True)

                if out.tell() <= max_bytes:
                    return out.getvalue()

        # 最後 fallback（一定回傳）
        return out.getvalue()
