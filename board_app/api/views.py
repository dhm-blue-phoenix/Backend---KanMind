from typing import Optional

from django.db.models import Q, QuerySet
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.http import Http404

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.request import Request

from .serializers import (
    UserEmailCheckSerializer, BoardSerializer, BoardDetailSerializer,
    BoardUpdateSerializer, TaskCreateSerializer, TaskListSerializer,
    TaskDetailSerializer, TaskUpdateSerializer, TaskSerializer, CommentSerializer,
    CommentCreateSerializer
)
from board_app.models import Board, Task, Comment


class EmailCheckView(generics.GenericAPIView):
    """
    GET /api/email-check/?email=...
    Checks if an email is registered.

    Query Params: email (required)
    Response: {id, email, fullname}
    Status: 200 if found, 400 if invalid, 404 if not found
    Requires authentication.
    """
    serializer_class = UserEmailCheckSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        email: Optional[str] = request.query_params.get('email')

        if not email:
            return Response(
                {'error': 'Die E-Mail-Adresse fehlt.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            validate_email(email)
        except ValidationError:
            return Response(
                {'error': 'Ungültige E-Mail-Format.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            user: User = User.objects.get(email=email)
            serializer: UserEmailCheckSerializer = self.get_serializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'error': 'E-Mail nicht gefunden.'},
                status=status.HTTP_404_NOT_FOUND
            )


class BoardListCreateView(generics.ListCreateAPIView):
    """
    GET /api/boards/
    Lists all boards the authenticated user owns or is member of

    Response: [{id, title, member_count, ticket_count, tasks_to_do_count, tasks_high_prio_count, owner_id}]

    POST /api/boards/
    Creates a new board with optional members

    Request Body:
    {
        "title": "string" (required),
        "members": [integer] (optional) – user IDs
    }

    Response: {id, title, member_count, ticket_count, tasks_to_do_count, tasks_high_prio_count, owner_id}
    """
    serializer_class = BoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        user = self.request.user
        if not user.is_authenticated:
            return Board.objects.none()
        return Board.objects.filter(
            Q(owner=user) | Q(members=user)
        ).distinct().prefetch_related('members', 'tasks')

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)

        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class BoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/boards/{board_id}/
    Returns detailed board info including members and tasks

    Response: {id, title, owner_id, members: [{id, email, fullname}], tasks: [...]}

    PATCH /api/boards/{board_id}/
    Updates title and/or members (owner only)

    Request Body:
    {
        "title": "string" (optional),
        "members": [integer] (optional) – user IDs
    }

    Response: {id, title, owner_data: {...}, members_data: [{...}]}

    DELETE /api/boards/{board_id}/
    Deletes the board (owner only) → 204 No Content
    """
    queryset = Board.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'board_id'

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return BoardDetailSerializer
        elif self.request.method in ['PUT', 'PATCH']:
            return BoardUpdateSerializer
        return BoardDetailSerializer

    def get_object(self) -> Board:
        board: Board = super().get_object()
        self._check_board_access(board)
        return board

    def _check_board_access(self, board: Board) -> None:
        is_owner = board.owner == self.request.user
        is_member = self.request.user in board.members.all()
        if not (is_owner or is_member):
            self.permission_denied(self.request)

    def perform_update(self, serializer) -> None:
        board: Board = self.get_object()
        if board.owner != self.request.user:
            self.permission_denied(self.request)
        serializer.save()

    def perform_destroy(self, instance: Board) -> None:
        if instance.owner != self.request.user:
            self.permission_denied(self.request)
        instance.delete()


class TaskCreateView(generics.CreateAPIView):
    """
    POST /api/tasks/
    Creates a new task in a board (board members only)

    Request Body:
    {
        "board": integer (required),
        "title": "string" (required),
        "description": "string" (optional),
        "status": "string" (required – To Do, In Progress, Done, ...),
        "priority": "string" (required – Low, Medium, High, Urgent),
        "assignee_id": integer (optional),
        "reviewer_id": integer (optional),
        "due_date": "YYYY-MM-DD" (optional)
    }

    Response: {id, title, description, status, priority, assignee, reviewer, due_date, comments_count}
    """
    serializer_class = TaskCreateSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request: Request, *args, **kwargs) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        task: Task = serializer.save(created_by=request.user)

        output_serializer = TaskListSerializer(
            task,
            context=self.get_serializer_context()
        )

        headers = self.get_success_headers(serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )


class AssignedToMeTasksView(generics.ListAPIView):
    """
    GET /api/tasks/assigned-to-me/
    Lists all tasks where the authenticated user is the assignee.

    Response: [{id, board, title, description, status, priority, assignee, reviewer, due_date, comments_count}]
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        user: User = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        return Task.objects.filter(assignee=user).select_related(
            'board', 'assignee', 'reviewer', 'created_by'
        )


class ReviewingTasksView(generics.ListAPIView):
    """
    GET /api/tasks/reviewing/
    Lists all tasks where the authenticated user is the reviewer.

    Response: [{id, board, title, description, status, priority, assignee, reviewer, due_date, comments_count}]
    """
    serializer_class = TaskListSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        user: User = self.request.user
        if not user.is_authenticated:
            return Task.objects.none()
        return Task.objects.filter(reviewer=user).select_related(
            'board', 'assignee', 'reviewer', 'created_by'
        )


class TaskDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /api/tasks/{task_id}/
    Returns task details

    Response: {id, title, description, status, priority, assignee, reviewer, due_date, comments_count}

    PATCH /api/tasks/{task_id}/
    Updates task fields (board members only)

    Request Body (partial):
    {
        "title": "string" (optional),
        "description": "string" (optional),
        "status": "string" (optional),
        "priority": "string" (optional),
        "assignee_id": integer (optional),
        "reviewer_id": integer (optional),
        "due_date": "YYYY-MM-DD" (optional)
    }

    Response: {id, title, description, status, priority, assignee, reviewer, due_date}

    DELETE /api/tasks/{task_id}/
    Deletes task (creator or board owner only) → 204 No Content
    """
    queryset = Task.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'task_id'

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return TaskUpdateSerializer
        return TaskDetailSerializer

    def get_object(self) -> Task:
        task: Task = super().get_object()
        self._check_task_access(task)
        return task

    def _check_task_access(self, task: Task) -> None:
        is_owner = task.board.owner == self.request.user
        is_member = self.request.user in task.board.members.all()
        if not (is_owner or is_member):
            self.permission_denied(self.request)

    def perform_update(self, serializer) -> None:
        task: Task = self.get_object()
        if task.board.owner != self.request.user and \
            self.request.user not in task.board.members.all():
            self.permission_denied(self.request)
        serializer.save()

    def update(self, request: Request, *args, **kwargs) -> Response:
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        context = self.get_serializer_context()
        context['customTaskResponse'] = 'patch'
        detail_serializer = TaskSerializer(instance, context=context)
        return Response(detail_serializer.data)

    def perform_destroy(self, instance: Task) -> None:
        is_creator = instance.created_by == self.request.user
        is_owner = instance.board.owner == self.request.user
        if not (is_creator or is_owner):
            self.permission_denied(self.request)
        instance.delete()


class TaskCommentsListCreateView(generics.ListCreateAPIView):
    """
    GET /api/tasks/{task_id}/comments/ - Lists all comments for a task
    POST /api/tasks/{task_id}/comments/ - Creates a new comment (board members only)
    
    GET Response: [{id, created_at, author, content}]
    POST Request: {content}
    POST Response: {id, created_at, author, content}
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self) -> QuerySet:
        task_id: int = int(self.kwargs.get('task_id'))
        task = self._get_task(task_id)

        if not task or not self._check_task_access(self.request, task):
            return Comment.objects.none()

        return Comment.objects.filter(task=task)

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CommentCreateSerializer
        return CommentSerializer

    def get_serializer_context(self) -> dict:
        context = super().get_serializer_context()
        task_id = int(self.kwargs.get('task_id'))
        task = self._get_task(task_id)
        context['task'] = task
        return context

    def _get_task(self, task_id: int) -> Optional[Task]:
        try:
            return Task.objects.get(id=task_id)
        except Task.DoesNotExist:
            return None

    def _check_task_access(self, request: Request, task: Task) -> bool:
        is_owner = task.board.owner == request.user
        is_member = request.user in task.board.members.all()
        return is_owner or is_member

    def list(self, request: Request, *args, **kwargs) -> Response:
        task_id = int(self.kwargs.get('task_id'))
        task = self._get_task(task_id)

        if not task:
            return Response(
                {"detail": "Task nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not self._check_task_access(request, task):
            return Response(
                {"detail": "Keine Berechtigung für diesen Task."},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().list(request, *args, **kwargs)

    def create(self, request: Request, *args, **kwargs) -> Response:
        task_id = int(self.kwargs.get('task_id'))
        task = self._get_task(task_id)

        if not task:
            return Response(
                {"detail": "Task nicht gefunden."},
                status=status.HTTP_404_NOT_FOUND
            )

        if not self._check_task_access(request, task):
            return Response(
                {"detail": "Keine Berechtigung für diesen Task."},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = CommentCreateSerializer(
            data=request.data,
            context={'task': task, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        comment = serializer.save()

        output_serializer = CommentSerializer(comment)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED
        )


class TaskCommentDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/tasks/{task_id}/comments/{comment_id}/
    Deletes a comment (only the comment author can delete it)

    Request Body: keiner erforderlich

    Response:
    - 204 No Content    → erfolgreich gelöscht
    - 404 Not Found     → Comment existiert nicht oder gehört nicht zu diesem Task
    - 403 Forbidden     → aktueller User ist nicht der Autor des Comments
    - 401 Unauthorized  → nicht authentifiziert
    """
    queryset = Comment.objects.all()
    permission_classes = [IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'comment_id'

    def get_object(self) -> Comment:
        comment: Comment = super().get_object()

        task_id = int(self.kwargs.get('task_id'))
        if comment.task_id != task_id:
            raise Http404("Comment gehört nicht zu diesem Task")

        return comment

    def perform_destroy(self, instance: Comment) -> None:
        if instance.author != self.request.user:
            self.permission_denied(self.request)
        instance.delete()