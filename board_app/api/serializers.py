# Django
from django.contrib.auth.models import User

# Django REST Framework
from rest_framework import serializers
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.exceptions import NotFound

# Local imports
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
    Handles creation with members and custom representation for stats.
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
        self.customTaskResposns = kwargs.pop('customTaskResposns', None)
        context = kwargs.get('context') or {}
        if not self.customTaskResposns and isinstance(context, dict):
            self.customTaskResposns = context.get('customTaskResposns')
        super().__init__(*args, **kwargs)

    def to_representation(self, instance):
        mode = self.customTaskResposns or (self.context or {}).get('customTaskResposns')

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
    Serializer for task lists (shows board id).
    Used for AssignedToMe and Reviewing lists.
    """
    assignee = UserEmailCheckSerializer(read_only=True)
    reviewer = UserEmailCheckSerializer(read_only=True)

    class Meta:
        model = Task
        fields = ['id', 'board', 'title', 'description', 'status', 'priority', 'assignee', 'reviewer', 'due_date', 'comments_count']

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
        fields = ['id', 'title', 'description', 'status', 'priority', 'assignee', 'reviewer', 'due_date', 'comments_count']

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
    Serializer for updating board (title/members via PATCH).
    Partial updates allowed.
    Returns owner_data and members_data in response.
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
    Validates status, priority, assignee/reviewer membership.
    """
    assignee_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True, source='assignee')
    reviewer_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True, source='reviewer')
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
    Serializer for updating tasks (partial).
    Validates status, priority, assignee/reviewer.
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
                        raise serializers.ValidationError({field: f"Der {field.replace('_id', '')} muss Mitglied des Boards sein."})
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
    """
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']

    def get_author(self, obj):
        return obj.author.get_full_name().strip() or obj.author.username


class CommentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating comments.
    Content only, author/task from context.
    """
    class Meta:
        model = Comment
        fields = ['content']

    def create(self, validated_data):
        task = self.context['task']
        author = self.context['request'].user
        return Comment.objects.create(task=task, author=author, **validated_data)