import base64
import json
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from django.conf import settings
from huggingface_hub import InferenceClient


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
            "You are an AR language tutor. Respond with STRICT JSON ONLY.\n"
            "No extra text, no markdown.\n"
            "Detect EXACTLY 2 OR 3 prominent visible objects "
            "(concrete physical nouns, not background or abstract concepts).\n"
            "OUTPUT STRUCTURE:\n"
            "{\n"
            "  \"vocabulary\": [ {\"word_en\": \"\", \"word_zh\": \"Traditional Chinese\", \"pos\": \"noun\"} ],\n"
            "  \"sentences\": [ {\"english\": \"\", \"chinese\": \"Traditional Chinese\"} ],\n"
            "}\n"
            "STRICT RULES:\n"
            "- vocabulary length MUST be exactly 2 or 3\n"
            "- sentences length MUST equal vocabulary length\n"
            "- Each chinese translation MUST be in Traditional Chinese\n"
            "- Each sentence MUST use EXACTLY ONE vocabulary word\n"
            "- Do NOT introduce new nouns\n"
            "- Output valid JSON only"
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
            input_language: str,
    ) -> List[Dict[str, Any]]:
        if analysis_enabled:
            prompt = (
                "You are an English tutor. Always respond in English."
                "Keep replies concise (1-2 sentences)."
                f"Input language: {input_language}."
                "Return STRICT JSON with keys:"
                "reply: string"
                "input_language: one of \"en\", \"zh\""
                "user_grammar: object or null"
                "assistant_grammar: object"
                "Rules:"
                "1.If input_language != \"en\", user_grammar must be null."
                "2.If input_language == \"en\", user_grammar must be an object even if correct."
                "3.user_grammar keys: is_correct (bool), corrected_text (string), errors (list), explanation (string)."
                "4.If correct, set is_correct true and corrected_text empty."
                "5.If incorrect, set is_correct false and provide corrected_text and errors."
                "6.assistant_grammar keys: summary (string), structures (list of 1-3 items)."
                "7.No extra text, no markdown, no code fences."
            )
        else:
            prompt = (
                "You are an English tutor. Always respond in English."
                "Keep replies concise (1-2 sentences)."
                "Return STRICT JSON with keys:"
                "reply: string"
                "No extra text, no markdown, no code fences."
            )

        messages: List[Dict[str, Any]] = [{"role": "system", "content": prompt}]
        messages.extend(conversation)
        return messages

    def build_vocab_messages(self, word: str) -> List[Dict[str, Any]]:
        prompt = (
            "You are an English tutor. Return STRICT JSON with keys:\n"
            "word: string\n"
            "ipa: string\n"
            "pos: string\n"
            "meaning_en: string\n"
            "meaning_zh: string (Traditional Chinese)\n"
            "example_en: string\n"
            "example_zh: string (Traditional Chinese)\n"
            "error: string or empty\n"
            "No extra text, no markdown, no code fences."
        )
        user_instruction = f"Analyze the English word: {word}"
        return [
            {"role": "system", "content": prompt},
            {"role": "user", "content": user_instruction},
        ]

    @staticmethod
    def detect_language(text: str) -> str:
        if re.search(r"[\u4E00-\u9FFF]", text):
            return "zh"
        if re.search(r"[A-Za-z]", text):
            return "en"
        return "other"


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
