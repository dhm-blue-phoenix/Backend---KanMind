# Standard library
from __future__ import annotations
from typing import Any, Dict

# Django
from django.contrib.auth.models import User

# Django REST Framework
from rest_framework import serializers

# Local imports
from board_app.models import Board, Task, Comment, STATUS_CHOICES, PRIORITY_CHOICES


class UserEmailCheckSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']

    def get_fullname(self, obj):
        return obj.get_full_name().strip() or obj.username


class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ['id', 'title', 'members', 'owner_id']
        read_only_fields = ['owner_id']

    def create(self, validated_data):
        members_data = validated_data.pop('members', [])
        request = self.context['request']
        board = Board.objects.create(owner=request.user, **validated_data)
        board.members.set(members_data)
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


class BoardDetailSerializer(serializers.ModelSerializer):
    members = UserEmailCheckSerializer(many=True, read_only=True)
    tasks = serializers.SerializerMethodField()

    class Meta:
        model = Board
        fields = ['id', 'title', 'owner_id', 'members', 'tasks']

    def get_tasks(self, obj):
        tasks = obj.tasks.all().select_related('assignee', 'reviewer')
        return TaskSerializer(tasks, many=True).data


class BoardUpdateSerializer(serializers.ModelSerializer):
    members = serializers.PrimaryKeyRelatedField(many=True, queryset=User.objects.all(), required=False)

    class Meta:
        model = Board
        fields = ['title', 'members']


class TaskSerializer(serializers.ModelSerializer):
    assignee = UserEmailCheckSerializer(read_only=True)
    reviewer = UserEmailCheckSerializer(read_only=True)

    class Meta:
        model = Task
        fields = [
            'id', 'board', 'title', 'description', 'status', 'priority',
            'assignee', 'reviewer', 'due_date', 'comments_count'
        ]

    def to_representation(self, instance):
        return {
            "id": instance.id,
            "board": instance.board_id,
            "title": instance.title,
            "description": instance.description or "",
            "status": instance.status,
            "priority": instance.priority,
            "assignee": UserEmailCheckSerializer(instance.assignee).data if instance.assignee else None,
            "reviewer": UserEmailCheckSerializer(instance.reviewer).data if instance.reviewer else None,
            "due_date": instance.due_date.isoformat() if instance.due_date else None,
            "comments_count": instance.comments_count()
        }


class TaskCreateSerializer(serializers.ModelSerializer):
    assignee_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True, source='assignee')
    reviewer_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True, source='reviewer')

    class Meta:
        model = Task
        fields = [
            'board', 'title', 'description', 'status', 'priority',
            'assignee_id', 'reviewer_id', 'due_date'
        ]

    def validate_status(self, value):
        if value not in dict(STATUS_CHOICES):
            raise serializers.ValidationError(f"Status muss einer von: {', '.join(dict(STATUS_CHOICES))} sein.")
        return value

    def validate_priority(self, value):
        if value not in dict(PRIORITY_CHOICES):
            raise serializers.ValidationError(f"Priority muss einer von: {', '.join(dict(PRIORITY_CHOICES))} sein.")
        return value

    def validate(self, data):
        board_input = data.get('board')
        
        if isinstance(board_input, Board):
            board = board_input
        else:
            try:
                board = Board.objects.get(id=board_input)
            except Board.DoesNotExist:
                raise serializers.ValidationError({"board": "Board nicht gefunden."})

        request = self.context['request']
        if request.user != board.owner and request.user not in board.members.all():
            raise serializers.ValidationError({"board": "Du bist kein Mitglied dieses Boards."})

        for field in ['assignee', 'reviewer']:
            user = data.get(field)
            if user and (user != board.owner and user not in board.members.all()):
                raise serializers.ValidationError({field: f"Der {field} muss Mitglied des Boards sein."})

        data['board'] = board
        return data

    def create(self, validated_data):
        request = self.context['request']
        validated_data['created_by'] = request.user
        return super().create(validated_data)


class TaskUpdateSerializer(serializers.ModelSerializer):
    assignee_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True, source='assignee')
    reviewer_id = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), required=False, allow_null=True, source='reviewer')

    class Meta:
        model = Task
        fields = [
            'title', 'description', 'status', 'priority',
            'assignee_id', 'reviewer_id', 'due_date'
        ]

    def validate_status(self, value):
        if value not in dict(STATUS_CHOICES):
            raise serializers.ValidationError(f"Status muss einer von: {', '.join(dict(STATUS_CHOICES))} sein.")
        return value

    def validate_priority(self, value):
        if value not in dict(PRIORITY_CHOICES):
            raise serializers.ValidationError(f"Priority muss einer von: {', '.join(dict(PRIORITY_CHOICES))} sein.")
        return value

    def validate(self, data):
        task = self.instance
        board = task.board

        for field in ['assignee', 'reviewer']:
            user = data.get(field)
            if user is not None and (user != board.owner and user not in board.members.all()):
                raise serializers.ValidationError({field: f"Der {field} muss Mitglied des Boards sein."})

        return data

    def to_representation(self, instance):
        return TaskSerializer(instance).data


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'created_at', 'author', 'content']

    def get_author(self, obj):
        return obj.author.get_full_name().strip() or obj.author.username


class CommentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['content']

    def create(self, validated_data):
        task = self.context['task']
        author = self.context['request'].user
        return Comment.objects.create(task=task, author=author, **validated_data)