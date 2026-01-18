# Django
from django.db.models import Q
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
    """
    GET /api/email-check/?email=...
    Checks if an email is registered.
    Returns user data if exists (200), else 404.
    Requires authentication.
    """
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
    """
    GET /api/boards/
    Lists all boards the authenticated user owns or is member of.

    POST /api/boards/
    Creates a new board. User is set as owner and added as member.
    """
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Board.objects.none()
        return Board.objects.filter(Q(owner=user) | Q(members=user)).distinct()


class BoardDetailView(APIView):
    """
    GET /api/boards/{board_id}/
    Returns detailed board info including members and tasks.

    PATCH /api/boards/{board_id}/
    Updates title and/or members (removes non-listed members).

    DELETE /api/boards/{board_id}/
    Deletes the board (only by owner).
    """
    permission_classes = [IsAuthenticated, IsBoardMember]

    def get_object(self, board_id):
        try:
            return Board.objects.get(id=board_id)
        except Board.DoesNotExist:
            return None

    def get(self, request, board_id):
        board = self.get_object(board_id)
        if not board:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = BoardDetailSerializer(board)
        return Response(serializer.data)

    def patch(self, request, board_id):
        board = self.get_object(board_id)
        if not board:
            return Response(status=status.HTTP_404_NOT_FOUND)

        serializer = BoardUpdateSerializer(board, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)

        # Explizit aktualisieren
        if 'title' in serializer.validated_data:
            board.title = serializer.validated_data['title']

        board.save()

        if 'members' in serializer.validated_data:
            board.members.set(serializer.validated_data['members'])

        # Board neu laden für frische Response
        board.refresh_from_db()

        return Response(BoardDetailSerializer(board).data)

    def delete(self, request, board_id):
        board = self.get_object(board_id)
        if not board:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if board.owner != request.user:
            return Response(status=status.HTTP_403_FORBIDDEN)

        board.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class TaskCreateView(generics.CreateAPIView):
    """
    POST /api/tasks/
    Creates a new task in a board.
    Only board members can create tasks.
    """
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated, IsBoardMember]

    def create(self, request, *args, **kwargs):
        # Serializer für Input verwenden
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Task speichern (created_by = aktueller User)
        task = serializer.save(created_by=request.user)

        # Response mit dem vollen nested TaskSerializer erzeugen
        full_serializer = TaskSerializer(task, context=self.get_serializer_context())

        headers = self.get_success_headers(serializer.data)
        return Response(full_serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class AssignedToMeTasksView(generics.ListAPIView):
    """
    GET /api/tasks/assigned-to-me/
    Lists tasks where the user is the assignee.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        return Task.objects.filter(assignee=user)


class ReviewingTasksView(generics.ListAPIView):
    """
    GET /api/tasks/reviewing/
    Lists tasks where the user is the reviewer.
    """
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        return Task.objects.filter(reviewer=user)


class TaskDetailView(APIView):
    """
    PATCH /api/tasks/{task_id}/
    Updates an existing task (partial, only board members).

    DELETE /api/tasks/{task_id}/
    Deletes a task (only creator or board owner).
    """
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
    """
    GET /api/tasks/{task_id}/comments/
    Lists all comments for a task.

    POST /api/tasks/{task_id}/comments/
    Creates a new comment for a task (only board members).
    """
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
    """
    DELETE /api/tasks/{task_id}/comments/{comment_id}/
    Deletes a comment (only by author).
    """
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