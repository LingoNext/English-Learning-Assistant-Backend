from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Conversation
from .serializers import ConversationSerializer


class ConversationViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Conversation CRUD operations
    - GET /api/conversations/ - 取得對話列表
    - POST /api/conversations/ - 建立新對話
    - GET /api/conversations/{id}/ - 取得特定對話
    - DELETE /api/conversations/{id}/ - 刪除對話（同時刪除所有相關訊息）
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
            "status": "success",
            "message": "對話列表取得成功",
            "data": serializer.data
        }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')

    def create(self, request, *args, **kwargs):
        """建立新對話"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({
            "status": "success",
            "message": "對話建立成功",
            "data": serializer.data
        }, status=status.HTTP_201_CREATED,content_type='application/json; charset=utf-8')

    def retrieve(self, request, *args, **kwargs):
        """取得特定對話"""
        try:
            conversation = self.get_queryset().get(pk=kwargs['pk'])
            serializer = self.get_serializer(conversation)
            return Response({
                "status": "success",
                "message": "對話取得成功",
                "data": serializer.data
            }, status=status.HTTP_200_OK,content_type='application/json; charset=utf-8')
        except Conversation.DoesNotExist:
            return Response({
                "status": "error",
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
                "status": "success",
                "message": "對話已刪除",
                "data": None
            }, status=status.HTTP_204_NO_CONTENT,content_type='application/json; charset=utf-8')
        except Conversation.DoesNotExist:
            return Response({
                "status": "error",
                "message": "對話不存在",
                "data": None
            }, status=status.HTTP_404_NOT_FOUND,content_type='application/json; charset=utf-8')

