from django.contrib.auth.models import User

from rest_framework import serializers
from rest_framework.exceptions import NotFound, PermissionDenied

from board_app.models import Board, Task, Comment, STATUS_CHOICES, PRIORITY_CHOICES


class UserEmailCheckSerializer(serializers.ModelSerializer):
    """
    Serializer for checking user by email.
    Returns id, email, and fullname.
    """
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return obj.get_full_name().strip() or obj.username


class BoardSerializer(serializers.ModelSerializer):
    """
    Serializer for Board list/create.

    POST Request Body:
    {
        "title": "string" (required),
        "members": [integer] (optional) – user IDs
    }
    """
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)

    class Meta:
        model = Board
        fields = ['id', 'title', 'members', 'owner_id']
        read_only_fields = ['owner_id']

    def create(self, validated_data):
        members_data = validated_data.pop('members', [])
        request = self.context['request']
        board = Board.objects.create(owner=request.user, **validated_data)
        board.members.set(members_data)
        if request.user not in members_data:
            board.members.add(request.user)
        return board

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "title": instance.title,
            "member_count": instance.member_count(),
            "ticket_count": instance.task_count(),
            "tasks_to_do_count": instance.tasks_to_do_count(),
            "tasks_high_prio_count": instance.tasks_high_prio_count(),
            "owner_id": instance.owner_id,
        }


class TaskSerializer(serializers.ModelSerializer):
    """
        Serializer for Task representation.
        Includes nested assignee/reviewer and custom output.
    """

    assignee = UserEmailCheckSerializer(read_only=True)
    reviewer = UserEmailCheckSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'due_date', 'comments_count'
        ]

    def __init__(self, *args, **kwargs):
        self.customTaskResponse = kwargs.pop('customTaskResponse', None)
        context = kwargs.get('context') or {}
        if not self.customTaskResponse and isinstance(context, dict):
            self.customTaskResponse = context.get('customTaskResponse')
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        mode = self.customTaskResponse or (self.context or {}).get('customTaskResponse')

        base = {
            "id": instance.id,
            "title": instance.title,
            "description": instance.description or "",
            "status": instance.status,
            "priority": instance.priority,
            "assignee": UserEmailCheckSerializer(instance.assignee).data if instance.assignee else None,
            "reviewer": UserEmailCheckSerializer(instance.reviewer).data if instance.reviewer else None,
            "due_date": instance.due_date.isoformat() if instance.due_date else None,
        }
        if mode == "patch":
            return base
        base["comments_count"] = instance.comments_count()
        return base


class TaskListSerializer(serializers.ModelSerializer):
    """
        Serializer for task list response.
        Includes nested assignee/reviewer and custom output.
    """

    assignee = UserEmailCheckSerializer(read_only=True)
    reviewer = UserEmailCheckSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'board', 'title', 'description', 'status', 'priority', 'assignee', 'reviewer', 'due_date',
                  'comments_count']

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'board': instance.board_id,
            'title': instance.title,
            'description': instance.description or "",
            'status': instance.status,
            'priority': instance.priority,
            'assignee': UserEmailCheckSerializer(instance.assignee).data if instance.assignee else None,
            'reviewer': UserEmailCheckSerializer(instance.reviewer).data if instance.reviewer else None,
            'due_date': instance.due_date.isoformat() if instance.due_date else None,
            'comments_count': instance.comments_count(),
        }


class TaskDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for task detail (hides board id).
    Used for BoardDetailView and TaskDetailView responses.
    """
    assignee = UserEmailCheckSerializer(read_only=True)
    reviewer = UserEmailCheckSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'status', 'priority', 'assignee', 'reviewer', 'due_date',
                  'comments_count']

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'title': instance.title,
            'description': instance.description or "",
            'status': instance.status,
            'priority': instance.priority,
            'assignee': UserEmailCheckSerializer(instance.assignee).data if instance.assignee else None,
            'reviewer': UserEmailCheckSerializer(instance.reviewer).data if instance.reviewer else None,
            'due_date': instance.due_date.isoformat() if instance.due_date else None,
            'comments_count': instance.comments_count(),
        }


class BoardDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for detailed board view (GET).
    Includes nested members (as list) and tasks.
    """
    members = UserEmailCheckSerializer(source='members', many=True, read_only=True)
    tasks = TaskDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']
        read_only_fields = ['id', 'owner_id', 'members', 'tasks']

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'title': instance.title,
            'owner_id': instance.owner_id,
            'members': UserEmailCheckSerializer(instance.members.all(), many=True).data,
            'tasks': TaskDetailSerializer(
                instance.tasks.all(), many=True,
                context=self.context or {}
            ).data
        }


class BoardUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating board (PATCH).

    Request Body (partial):
    {
        "title": "string" (optional),
        "members": [integer] (optional) – user IDs
    }
    """
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)

    class Meta:
        model = Board
        fields = ['title', 'members']

    def to_representation(self, instance):
        return {
            'id': instance.id,
            'title': instance.title,
            'owner_data': UserEmailCheckSerializer(instance.owner).data,
            'members_data': UserEmailCheckSerializer(instance.members.all(), many=True).data,
        }


class TaskCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating tasks.

    Request Body:
    {
        "board": integer (required),
        "title": "string" (required),
        "description": "string" (optional),
        "status": "string" (required),
        "priority": "string" (required),
        "assignee_id": integer (optional),
        "reviewer_id": integer (optional),
        "due_date": "YYYY-MM-DD" (optional)
    }
    """
    assignee_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True,
                                                     source='assignee')
    reviewer_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True,
                                                     source='reviewer')
    board = serializers.IntegerField(write_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority',
            'assignee_id', 'reviewer_id', 'due_date',
        ]

    def validate_status(self, value):
        if value not in dict(STATUS_CHOICES):
            raise serializers.ValidationError(f"Status muss einer von: {', '.join(dict(STATUS_CHOICES))} sein.")
        return value

    def validate_priority(self, value):
        if value not in dict(PRIORITY_CHOICES):
            raise serializers.ValidationError(f"Priority muss einer von: {', '.join(dict(PRIORITY_CHOICES))} sein.")
        return value

    def validate(self, attrs):
        board_id = attrs.get('board')

        if isinstance(board_id, Board):
            board = board_id
        else:
            try:
                board = Board.objects.get(id=board_id)
            except Board.DoesNotExist:
                raise NotFound(detail={"board": "Board nicht gefunden."})

        request = self.context['request']
        if request.user != board.owner and request.user not in board.members.all():
            raise PermissionDenied({"board": "Du bist kein Mitglied dieses Boards."})

        for field in ['assignee', 'reviewer']:
            user = attrs.get(field)
            if user and (user != board.owner and user not in board.members.all()):
                raise serializers.ValidationError({field: f"Der {field} muss Mitglied des Boards sein."})

        attrs['board'] = board
        return attrs

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        return super().create(validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating tasks (PATCH).

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
    """
    assignee_id = serializers.IntegerField(write_only=True, required=False)
    reviewer_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Task
        fields = ['title', 'description', 'status', 'priority', 'assignee_id', 'reviewer_id', 'due_date']

    def validate_status(self, value):
        if value not in dict(STATUS_CHOICES):
            raise serializers.ValidationError(f"Status muss einer von: {', '.join(dict(STATUS_CHOICES))} sein.")
        return value

    def validate_priority(self, value):
        if value not in dict(PRIORITY_CHOICES):
            raise serializers.ValidationError(f"Priority muss einer von: {', '.join(dict(PRIORITY_CHOICES))} sein.")
        return value

    def validate(self, attrs):
        instance = self.instance
        board = instance.board
        request = self.context.get('request')

        for field in ['assignee_id', 'reviewer_id']:
            user_id = attrs.get(field)
            if user_id is not None:
                try:
                    user = User.objects.get(id=user_id)
                    if user != board.owner and user not in board.members.all():
                        raise serializers.ValidationError(
                            {field: f"Der {field.replace('_id', '')} muss Mitglied des Boards sein."})
                except User.DoesNotExist:
                    raise serializers.ValidationError({field: f"User mit ID {user_id} existiert nicht"})

        return attrs

    def update(self, instance, validated_data):
        assignee_id = validated_data.pop('assignee_id', None)
        reviewer_id = validated_data.pop('reviewer_id', None)

        if assignee_id is not None:
            try:
                instance.assignee = User.objects.get(id=assignee_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({"assignee_id": f"User mit ID {assignee_id} existiert nicht"})

        if reviewer_id is not None:
            try:
                instance.reviewer = User.objects.get(id=reviewer_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({"reviewer_id": f"User mit ID {reviewer_id} existiert nicht"})

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance


class CommentSerializer(serializers.ModelSerializer):
    """
    Serializer for Comment representation.
    Author as full name.
    Returns: id, created_at (ISO format), author (fullname), content
    """
    author = serializers.SerializerMethodField()
    created_at = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']

    def get_author(self, obj):
        return obj.author.get_full_name().strip() or obj.author.username

    def get_created_at(self, obj):
        # Return ISO format: "2025-02-20T14:30:00Z"
        return obj.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating comments.

    Request Body:
    {
        "content": "string" (required)
    }
    """

    class Meta:
        model = Comment
        fields = ['content']

    def validate_content(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Der Inhalt des Kommentars darf nicht leer sein.")
        return value

    def create(self, validated_data):
        task = self.context['task']
        author = self.context['request'].user
        return Comment.objects.create(task=task, author=author, **validated_data)