from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import ConversationListSerializer, MessageListSerializer

class ConversationAllView(APIView):
    """
    GET /chat/conversations/all/ - 取得對話列表
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """取得對話列表"""
        queryset = Conversation.objects.filter(user=request.user).order_by('-updated_at')
        serializer = ConversationListSerializer(queryset, many=True)
        return Response({
            "message": "對話列表取得成功",
            "data": serializer.data
        }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')


class ConversationDetailView(APIView):
    """
    POST /chat/conversation/ - 取得特定對話的訊息
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """取得特定對話的訊息"""
        conversation_id = request.data.get('conversation_id')
        if not conversation_id:
            return Response({
                "message": "缺少必要參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            messages = Message.objects.filter(conversation=conversation).order_by('timestamp')
            serializer = MessageListSerializer(messages, many=True)
            return Response({
                "message": "對話訊息取得成功",
                "data": serializer.data
            }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')
        except Conversation.DoesNotExist:
            return Response({
                "message": "對話不存在或無權限",
                "data": None
            }, status=status.HTTP_401_UNAUTHORIZED, content_type='application/json; charset=utf-8')


class ConversationView(APIView):
    """
    POST /chat/conversations/ - 建立新對話
    DELETE /chat/conversations/ - 刪除對話
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """建立新對話（同時建立第一則訊息）"""
        text = request.data.get('text')
        is_user = request.data.get('is_user')

        if not text or is_user is None:
            return Response({
                "message": "缺少必要參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        # 建立新對話
        conversation = Conversation.objects.create(user=request.user)

        # 建立第一則訊息
        Message.objects.create(
            conversation=conversation,
            text=text,
            is_user=is_user
        )

        return Response({
            "message": "對話建立成功",
            "data": {"conversation_id": conversation.id}
        }, status=status.HTTP_201_CREATED, content_type='application/json; charset=utf-8')

    def delete(self, request):
        """刪除對話"""
        conversation_id = request.data.get('conversation_id')
        if not conversation_id:
            return Response({
                "message": "缺少必要參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            conversation.delete()
            return Response({
                "message": "對話已刪除",
                "data": None
            }, status=status.HTTP_204_NO_CONTENT, content_type='application/json; charset=utf-8')
        except Conversation.DoesNotExist:
            return Response({
                "message": "對話不存在或無權限",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND, content_type='application/json; charset=utf-8')


class MessageView(APIView):
    """
    POST /chat/messages/ - 建立新訊息
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """建立新訊息"""
        conversation_id = request.data.get('conversation_id')
        text = request.data.get('text')
        is_user = request.data.get('is_user')

        if not conversation_id or not text or is_user is None:
            return Response({
                "message": "缺少必要參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        # 驗證對話是否存在且屬於當前用戶
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({
                "message": "對話不存在或無權限",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND, content_type='application/json; charset=utf-8')

        # 建立新訊息
        Message.objects.create(
            conversation=conversation,
            text=text,
            is_user=is_user
        )

        # 更新對話的 updated_at 時間
        conversation.save()

        return Response({
            "message": "訊息建立成功",
            "data": None
        }, status=status.HTTP_201_CREATED, content_type='application/json; charset=utf-8')
