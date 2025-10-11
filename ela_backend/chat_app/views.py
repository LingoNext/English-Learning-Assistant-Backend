from rest_framework import viewsets, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Conversation, Message
from .serializers import ConversationSerializer, MessageSerializer

class ConversationViewSet(viewsets.ModelViewSet):
    queryset = Conversation.objects.all()
    serializer_class = ConversationSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 只取目前登入使用者的對話
        return Conversation.objects.filter(user=self.request.user, is_active=True)
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            "status": "success",
            "message": "Conversations retrieved successfully",
            "data": serializer.data
        })
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response({
            "status": "success",
            "message": "Conversation created successfully",
            "data": serializer.data
        }, status=201)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        conversation_id = self.kwargs['pk']
        return Message.objects.filter(conversation_id=conversation_id).order_by('created_at')


class ChatMessageCreateView(generics.CreateAPIView):
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        conversation = Conversation.objects.get(id=pk, user=request.user)
        user_message = Message.objects.create(
            conversation=conversation,
            user=request.user,
            role='user',
            content=request.data.get('message', '')
        )

        # 假設這裡呼叫 LLM 推理服務
        ai_reply_content = f"AI 回覆: {user_message.content}"
        ai_message = Message.objects.create(
            conversation=conversation,
            user=request.user,
            role='ai',
            content=ai_reply_content
        )

        serializer = MessageSerializer(ai_message)
        return Response({
            'status': 'success',
            'message': 'Message processed successfully',
            'data': serializer.data
        })
