# Django REST Framework
from rest_framework.permissions import BasePermission

# Local imports
from board_app.models import Board, Task, Comment


class IsBoardMember(BasePermission):
    """
    Allows access if user is member or owner of the board.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Board):
            return obj.owner == request.user or request.user in obj.members.all()
        elif isinstance(obj, Task):
            return obj.board.owner == request.user or request.user in obj.board.members.all()
        elif isinstance(obj, Comment):
            return obj.task.board.owner == request.user or request.user in obj.task.board.members.all()
        return False


class IsBoardOwner(BasePermission):
    """
    Allows access only if user is owner of the board.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Board):
            return obj.owner == request.user
        return False


class IsTaskCreatorOrBoardOwner(BasePermission):
    """
    Allows access if user is task creator or board owner.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Task):
            return obj.created_by == request.user or obj.board.owner == request.user
        return False


class IsCommentAuthor(BasePermission):
    """
    Allows access if user is author of the comment.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Comment):
            return obj.author == request.user
        return False