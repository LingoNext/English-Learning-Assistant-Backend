from rest_framework import serializers

# 單詞項目序列化器
class VocabularyItemSerializer(serializers.Serializer):
    word_en = serializers.CharField()
    word_zh = serializers.CharField()
    pos = serializers.CharField()

# 句子項目序列化器
class SentenceItemSerializer(serializers.Serializer):
    english = serializers.CharField()
    chinese = serializers.CharField()

# 圖片分析響應序列化器
class VisualAnalysisSerializer(serializers.Serializer):
    """用於 POST /llm/visual_analysis/ 端點的簡化序列化器"""
    vocabulary = VocabularyItemSerializer(many=True, required=False, allow_empty=True)
    sentences = SentenceItemSerializer(many=True, required=False, allow_empty=True)

# 用戶語法分析序列化器
class UserGrammarSerializer(serializers.Serializer):
    is_correct = serializers.BooleanField()
    corrected_text = serializers.CharField(required=False, allow_blank=True)
    errors = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        allow_empty=True
    )
    explanation = serializers.CharField(required=False, allow_blank=True)

# 語法結構序列化器
class GrammarStructureSerializer(serializers.Serializer):
    type = serializers.CharField()
    description = serializers.CharField()
    example = serializers.CharField()

# 對話響應序列化器
class ChatResponseSerializer(serializers.Serializer):
    """用於 POST /llm/chat/ 端點的簡化序列化器"""
    reply = serializers.CharField()
    title = serializers.CharField(required=False, allow_blank=True)
    user_grammar = UserGrammarSerializer(required=False, allow_null=True)
    grammar_structure = GrammarStructureSerializer(required=False, allow_null=True)

# 單詞解析響應序列化器
class VocabResponseSerializer(serializers.Serializer):
    """用於 POST /llm/vocab/ 端點的簡化序列化器"""
    word = serializers.CharField()
    ipa = serializers.CharField(required=False, allow_blank=True)
    pos = serializers.CharField(required=False, allow_blank=True)
    meaning_en = serializers.CharField(required=False, allow_blank=True)
    meaning_zh = serializers.CharField(required=False, allow_blank=True)
    example_en = serializers.CharField(required=False, allow_blank=True)
    example_zh = serializers.CharField(required=False, allow_blank=True)
    error = serializers.CharField(required=False, allow_blank=True)
