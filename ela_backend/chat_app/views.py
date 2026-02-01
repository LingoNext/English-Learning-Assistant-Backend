from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Conversation CRUD operations
    - GET /chat/conversations/ - 取得對話列表
    - POST /chat/conversations/ - 建立新對話
    - GET /chat/conversations/{id}/ - 取得特定對話
    - DELETE /chat/conversations/{id}/ - 刪除對話（同時刪除所有相關訊息）
    """
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只取目前登入使用者的對話
        return Conversation.objects.filter(user=self.request.user).order_by('-updated_at')

    def list(self, request, *args, **kwargs):
        """取得對話列表"""
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "對話列表取得成功",
            "data": serializer.data
        }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')

    def create(self, request, *args, **kwargs):
        """建立新對話"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({
            "message": "對話建立成功",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED,content_type='application/json; charset=utf-8')

    def retrieve(self, request, *args, **kwargs):
        """取得特定對話"""
        try:
            conversation = self.get_queryset().get(pk=kwargs['pk'])
            serializer = self.get_serializer(conversation)
            return Response({
                "message": "對話取得成功",
                "data": serializer.data
            }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')
        except Conversation.DoesNotExist:
            return Response({
                "message": "對話不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND,content_type='application/json; charset=utf-8')

    def destroy(self, request, *args, **kwargs):
        """刪除對話（同時刪除所有相關訊息）"""
        try:
            conversation = self.get_queryset().get(pk=kwargs['pk'])
            # 由於 Message 的 ForeignKey 設定了 on_delete=CASCADE，刪除對話時會自動刪除相關訊息
            conversation.delete()
            return Response({
                "message": "對話已刪除",
                "data": None
            }, status=status.HTTP_204_NO_CONTENT,content_type='application/json; charset=utf-8')
        except Conversation.DoesNotExist:
            return Response({
                "message": "對話不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND,content_type='application/json; charset=utf-8')


class MessageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Message CRUD operations
    - GET /chat/messages/?conversation_id={id} - 取得特定對話的所有訊息
    - POST /chat/messages/ - 建立新訊息
    - GET /chat/messages/{id}/ - 取得特定訊息
    - DELETE /chat/messages/{id}/ - 刪除訊息
    """
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """只取得目前登入使用者的對話中的訊息"""
        queryset = Message.objects.filter(conversation__user=self.request.user)

        # 支援按 conversation_id 過濾
        conversation_id = self.request.query_params.get('conversation_id')
        if conversation_id:
            queryset = queryset.filter(conversation_id=conversation_id)

        return queryset.order_by('timestamp')

    def list(self, request, *args, **kwargs):
        """取得訊息列表"""
        conversation_id = request.query_params.get('conversation_id')
        if not conversation_id:
            return Response({
                "message": "需要提供 conversation_id 參數",
                "data": None
            }, status=status.HTTP_400_BAD_REQUEST, content_type='application/json; charset=utf-8')

        # 驗證對話是否屬於當前用戶
        try:
            Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({
                "message": "對話不存在或無權限",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND, content_type='application/json; charset=utf-8')

        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "message": "訊息列表取得成功",
            "data": serializer.data
        }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')

    def create(self, request, *args, **kwargs):
        """建立新訊息"""
        conversation_id = request.data.get('conversation')

        # 驗證對話是否存在且屬於當前用戶
        try:
            conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            return Response({
                "message": "對話不存在或無權限",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND, content_type='application/json; charset=utf-8')

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # 更新對話的 updated_at 時間
        conversation.save()

        return Response({
            "status": "success",
            "message": "訊息建立成功",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED, content_type='application/json; charset=utf-8')

    def retrieve(self, request, *args, **kwargs):
        """取得特定訊息"""
        try:
            message = self.get_queryset().get(pk=kwargs['pk'])
            serializer = self.get_serializer(message)
            return Response({
                "message": "訊息取得成功",
                "data": serializer.data
            }, status=status.HTTP_200_OK, content_type='application/json; charset=utf-8')
        except Message.DoesNotExist:
            return Response({
                "message": "訊息不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND, content_type='application/json; charset=utf-8')

    def destroy(self, request, *args, **kwargs):
        """刪除訊息"""
        try:
            message = self.get_queryset().get(pk=kwargs['pk'])
            message.delete()
            return Response({
                "message": "訊息已刪除",
                "data": None
            }, status=status.HTTP_204_NO_CONTENT, content_type='application/json; charset=utf-8')
        except Message.DoesNotExist:
            return Response({
                "message": "訊息不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND, content_type='application/json; charset=utf-8')

