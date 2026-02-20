from rest_framework import serializers


class VocabularyItemSerializer(serializers.Serializer):
    """單詞項目序列化器"""
    word_en = serializers.CharField()
    word_zh = serializers.CharField()
    pos = serializers.CharField(required=False, allow_blank=True)


class SentenceItemSerializer(serializers.Serializer):
    """句子項目序列化器"""
    english = serializers.CharField()
    chinese = serializers.CharField()


class VisualAnalysisSerializer(serializers.Serializer):
    """圖片分析響應序列化器"""
    vocabulary = VocabularyItemSerializer(many=True, required=False, allow_empty=True)
    sentences = SentenceItemSerializer(many=True, required=False, allow_empty=True)


class GrammarErrorSerializer(serializers.Serializer):
    """語法錯誤序列化器"""
    error = serializers.CharField()
    correction = serializers.CharField(required=False, allow_blank=True)
    explanation = serializers.CharField(required=False, allow_blank=True)


class UserGrammarSerializer(serializers.Serializer):
    """用戶語法分析序列化器"""
    is_correct = serializers.BooleanField()
    corrected_text = serializers.CharField(required=False, allow_blank=True)
    errors = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    explanation = serializers.CharField(required=False, allow_blank=True)


class GrammarStructureSerializer(serializers.Serializer):
    """語法結構序列化器"""
    type = serializers.CharField()
    description = serializers.CharField()
    example = serializers.CharField(required=False, allow_blank=True)


class AssistantGrammarSerializer(serializers.Serializer):
    """助手語法分析序列化器"""
    summary = serializers.CharField()
    structures = GrammarStructureSerializer(many=True, required=False, allow_empty=True)


class ChatResponseSerializer(serializers.Serializer):
    """對話響應序列化器"""
    reply = serializers.CharField()
    input_language = serializers.CharField()
    user_grammar = UserGrammarSerializer(required=False, allow_null=True)
    assistant_grammar = AssistantGrammarSerializer(required=False, allow_null=True)
    raw_text = serializers.CharField(required=False, allow_blank=True)


class VocabResponseSerializer(serializers.Serializer):
    """單詞解析響應序列化器"""
    word = serializers.CharField()
    ipa = serializers.CharField(required=False, allow_blank=True)
    pos = serializers.CharField(required=False, allow_blank=True)
    meaning_en = serializers.CharField(required=False, allow_blank=True)
    meaning_zh = serializers.CharField(required=False, allow_blank=True)
    example_en = serializers.CharField(required=False, allow_blank=True)
    example_zh = serializers.CharField(required=False, allow_blank=True)
    error = serializers.CharField(required=False, allow_blank=True)


class ErrorResponseSerializer(serializers.Serializer):
    """錯誤響應序列化器"""
    message = serializers.CharField()
