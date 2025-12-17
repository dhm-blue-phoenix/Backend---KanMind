# Standard library
from typing import Any

# Django
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import HttpRequest

# Django REST Framework
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Local imports
from .permissions import IsBoardMember, IsBoardOwner, IsTaskCreatorOrBoardOwner, IsCommentAuthor
from .serializers import (
    UserEmailCheckSerializer, BoardSerializer, BoardDetailSerializer,
    BoardUpdateSerializer, TaskCreateSerializer, TaskSerializer,
    TaskUpdateSerializer, CommentSerializer, CommentCreateSerializer
)
from board_app.models import Board, Task, Comment


class EmailCheckView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest) -> Response:
        email = request.query_params.get('email')
        if not email:
            return Response({'error': 'Die E-Mail-Adresse fehlt.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_email(email)
        except ValidationError:
            return Response({'error': 'Ungültige E-Mail-Format.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
            serializer = UserEmailCheckSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response({'error': 'E-Mail nicht gefunden.'}, status=status.HTTP_404_NOT_FOUND)


class BoardListCreateView(generics.ListCreateAPIView):
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Board.objects.filter(owner=user) | Board.objects.filter(members=user)


class BoardDetailView(APIView):
    permission_classes = [IsAuthenticated, IsBoardMember]

    def get(self, request, board_id):
        board = self.get_object(board_id)
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data)

    def patch(self, request, board_id):
        board = self.get_object(board_id)
        serializer = BoardUpdateSerializer(board, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        if 'members' in request.data:
            board.members.set(serializer.validated_data['members'])
        serializer.save()
        return Response(BoardSerializer(board).data)

    def delete(self, request, board_id):
        board = self.get_object(board_id)
        self.check_object_permissions(request, board)  # Extra für Owner, da IsBoardMember nicht genug
        if board.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        board.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def get_object(self, board_id):
        try:
            return Board.objects.get(id=board_id)
        except Board.DoesNotExist:
            raise Response(status=status.HTTP_404_NOT_FOUND)


class TaskCreateView(generics.CreateAPIView):
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated, IsBoardMember]


class AssignedToMeTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(assignee=self.request.user)


class ReviewingTasksView(generics.ListAPIView):
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Task.objects.filter(reviewer=self.request.user)


class TaskDetailView(APIView):
    permission_classes = [IsAuthenticated, IsBoardMember]

    def get_object(self, task_id):
        try:
            return Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return None

    def patch(self, request, task_id):
        task = self.get_object(task_id)
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = TaskUpdateSerializer(task, data=request.data, partial=True, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, task_id):
        task = self.get_object(task_id)
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        if task.created_by != request.user and task.board.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)
        task.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskCommentsListCreateView(APIView):
    permission_classes = [IsAuthenticated, IsBoardMember]

    def get_task(self, task_id):
        try:
            return Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return None

    def get(self, request, task_id):
        task = self.get_task(task_id)
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        comments = task.comments.all()
        serializer = CommentSerializer(comments, many=True)
        return Response(serializer.data)

    def post(self, request, task_id):
        task = self.get_task(task_id)
        if not task:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = CommentCreateSerializer(data=request.data, context={'task': task, 'request': request})
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()
        return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class TaskCommentDeleteView(APIView):
    permission_classes = [IsAuthenticated, IsCommentAuthor]

    def get_comment(self, comment_id):
        try:
            return Comment.objects.get(id=comment_id)
        except Comment.DoesNotExist:
            return None

    def delete(self, request, task_id, comment_id):
        comment = self.get_comment(comment_id)
        if not comment or comment.task.id != task_id:
            return Response(status=status.HTTP_404_NOT_FOUND)
        comment.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)