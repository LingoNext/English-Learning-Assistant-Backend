from typing import Any, Dict, List
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from .services import get_novita_client
from rest_framework.permissions import AllowAny
from .serializers import (
    VisualAnalysisSerializer,
    ChatResponseSerializer,
    VocabResponseSerializer,
    ErrorResponseSerializer
)
import re


def _trim_reply(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        return cleaned
    parts = re.split(r"(?<=[.!?])\s+", cleaned)
    if len(parts) <= 2:
        return cleaned
    return " ".join(parts[:2]).strip()


class VisualView(APIView):
    """ POST /llm/analyze/ - 接收圖片並返回雙語 AR 學習內容 """
    permission_classes = [AllowAny]
    def post(self, request):
        image = request.FILES.get("image")
        if not image:
            error_serializer = ErrorResponseSerializer({"message": "缺少必要參數"})
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST,
                            content_type='application/json; charset=utf-8')

        try:
            client = get_novita_client()
            inference = client.analyze_image(image.read())
        except Exception as e:
            error_serializer = ErrorResponseSerializer({"message": str(e)})
            return Response(error_serializer.data, status=status.HTTP_502_BAD_GATEWAY,
                            content_type='application/json; charset=utf-8')

        parsed: Dict[str, Any] = inference.get("parsed") or {}

        vocabulary: List[Dict[str, Any]] = parsed.get("vocabulary") or []
        sentences: List[Dict[str, str]] = parsed.get("sentences") or []

        response_data = {
            "vocabulary": vocabulary,
            "sentences": sentences
        }

        serializer = VisualAnalysisSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')


class ChatView(APIView):
    """ POST /llm/chat/ - 以對話形式與模型互動，並可選擇是否啟用語法分析 """
    permission_classes = [AllowAny]
    def post(self, request):
        messages = request.data.get("messages")
        analysis_enabled = bool(request.data.get("analysis_enabled", False))

        conversation: List[Dict[str, str]] = []
        if isinstance(messages, list) and messages:
            for item in messages:
                if not isinstance(item, dict):
                    continue
                role = item.get("role")
                content = item.get("content")
                if role not in ("user", "assistant"):
                    continue
                if not isinstance(content, str) or not content.strip():
                    continue
                conversation.append({"role": role, "content": content.strip()})

        if not conversation:
            text_input = str(request.data.get("text", "")).strip()
            if not text_input:
                error_serializer = ErrorResponseSerializer({"message": "缺少必要參數"})
                return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST,
                                content_type='application/json; charset=utf-8')
            conversation = [{"role": "user", "content": text_input}]

        last_user = next((m["content"] for m in reversed(conversation) if m["role"] == "user"), "")
        if not last_user:
            error_serializer = ErrorResponseSerializer({"message": "at least one user message is required."})
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST,
                            content_type='application/json; charset=utf-8')

        try:
            client = get_novita_client()
        except Exception as e:
            error_serializer = ErrorResponseSerializer({"message": str(e)})
            return Response(error_serializer.data, status=status.HTTP_502_BAD_GATEWAY,
                            content_type='application/json; charset=utf-8')

        input_language = client.detect_language(last_user)
        prompt_messages = client.build_chat_messages(conversation, analysis_enabled, input_language)

        try:
            inference = client.analyze_text(prompt_messages)
        except Exception as e:
            error_serializer = ErrorResponseSerializer({"message": str(e)})
            return Response(error_serializer.data, status=status.HTTP_502_BAD_GATEWAY,
                            content_type='application/json; charset=utf-8')

        parsed: Dict[str, Any] = inference.get("parsed") or {}
        user_grammar = parsed.get("user_grammar") if isinstance(parsed, dict) else None
        assistant_grammar = parsed.get("assistant_grammar") if isinstance(parsed, dict) else None
        reply = parsed.get("reply") if isinstance(parsed, dict) else None
        if not isinstance(reply, str) or not reply.strip():
            raw_text = inference.get("raw_text")
            reply = raw_text if isinstance(raw_text, str) else ""

        reply = _trim_reply(reply)

        if analysis_enabled:
            if input_language == "en" and not isinstance(user_grammar, dict):
                user_grammar = {
                    "is_correct": False,
                    "corrected_text": "",
                    "errors": ["No grammar analysis returned."],
                    "explanation": "",
                }
            if not isinstance(assistant_grammar, dict):
                assistant_grammar = {
                    "summary": "No grammar analysis returned.",
                    "structures": [],
                }
        else:
            user_grammar = None
            assistant_grammar = None

        response_data = {
            "reply": reply,
            "input_language": parsed.get("input_language") if isinstance(parsed, dict) else input_language,
            "user_grammar": user_grammar,
            "assistant_grammar": assistant_grammar,
            "raw_text": inference.get("raw_text", ""),
        }

        serializer = ChatResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')


class VocabView(APIView):
    """ POST /llm/vocab/ - 單字解析 """
    permission_classes = [AllowAny]
    def post(self, request):
        word = request.data.get("word")
        if not word:
            error_serializer = ErrorResponseSerializer({"message": "缺少必要參數"})
            return Response(error_serializer.data, status=status.HTTP_400_BAD_REQUEST,
                            content_type='application/json; charset=utf-8')
        try:
            client = get_novita_client()
            prompt_messages = client.build_vocab_messages(word)
            inference = client.analyze_text(prompt_messages)
        except Exception as e:
            error_serializer = ErrorResponseSerializer({"message": str(e)})
            return Response(error_serializer.data, status=status.HTTP_502_BAD_GATEWAY,
                            content_type='application/json; charset=utf-8')

        parsed: Dict[str, Any] = inference.get("parsed") or {}

        response_data = {
            "word": parsed.get("word") if isinstance(parsed, dict) else word,
            "ipa": parsed.get("ipa") if isinstance(parsed, dict) else "",
            "pos": parsed.get("pos") if isinstance(parsed, dict) else "",
            "meaning_en": parsed.get("meaning_en") if isinstance(parsed, dict) else "",
            "meaning_zh": parsed.get("meaning_zh") if isinstance(parsed, dict) else "",
            "example_en": parsed.get("example_en") if isinstance(parsed, dict) else "",
            "example_zh": parsed.get("example_zh") if isinstance(parsed, dict) else "",
            "error": parsed.get("error") if isinstance(parsed, dict) else ""
        }

        serializer = VocabResponseSerializer(response_data)
        return Response(serializer.data, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')
