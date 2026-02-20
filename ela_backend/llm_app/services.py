import base64
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from django.conf import settings
from huggingface_hub import InferenceClient


def _estimate_token_count(text: str) -> int:
    """Rough estimate of token count for text (1 token ≈ 4 chars for most text)"""
    return len(text) // 4


def _calculate_conversation_tokens(messages: List[Dict[str, str]]) -> int:
    """Calculate total estimated tokens in a conversation"""
    total_chars = sum(len(msg.get("content", "")) for msg in messages)
    return _estimate_token_count(str(total_chars))


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
            "max_tokens": 512,
            "temperature": 0.4,
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
            "max_tokens": 512,
            "temperature": 0.4,
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
            max_context_tokens: int = 1500,
    ) -> List[Dict[str, Any]]:
        # Check if conversation is too long and needs summarization
        conversation_tokens = _calculate_conversation_tokens(conversation)

        if conversation_tokens > max_context_tokens and len(conversation) > 6:
            # Keep the last few messages and summarize the rest
            recent_messages = conversation[-4:]  # Keep last 4 messages for context
            older_messages = conversation[:-4]

            if older_messages:
                summary = self._summarize_conversation(older_messages)
                # Create summarized conversation
                conversation = [
                                   {"role": "system", "content": f"Previous conversation summary: {summary}"}
                               ] + recent_messages

        if analysis_enabled:

            prompt = (
                "English tutor. JSON only.\n"
                "Format:\n"
                "{\n"
                "  \"reply\": \"1-2 sentences, no repeat\",\n"
                "  \"user_grammar\": {\n"
                "    \"is_correct\": bool,\n"
                "    \"corrected_text\": \"if wrong\",\n"
                "    \"errors\": [\"list\"],\n"
                "    \"explanation\": \"Traditional Chinese\"\n"
                "  },\n"
                "  \"grammar_structure\": {\n"
                "    \"type\": \"structure type\",\n"
                "    \"description\": \"brief desc\",\n"
                "    \"example\": \"optional\"\n"
                "  }\n"
                "}\n"
                "Analyze user's last message only."
            )
        else:
            prompt = (
                "English tutor. JSON only:\n"
                "{\"reply\": \"Natural response, don't repeat user input\"}\n"
                "1-2 sentences max.")
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
        prompt = (
            "English tutor. JSON only:\n"
            "{\"word\":\"\",\"ipa\":\"\",\"pos\":\"\",\"meaning_en\":\"\",\"meaning_zh\":\"Traditional Chinese\",\"example_en\":\"\",\"example_zh\":\"Traditional Chinese\",\"error\":\"\"}"
            "Rules: Each chinese translation MUST be in traditional chinese"
        )
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
