from rest_framework.permissions import BasePermission

from board_app.models import Board, Task, Comment


class IsBoardMember(BasePermission):
    """
    Grants access if the user is a member or owner of the board.
    Works for Board, Task, and Comment objects.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

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
    Grants access only if the user is the owner of the board.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Board):
            return obj.owner == request.user
        return False


class IsTaskCreatorOrBoardOwner(BasePermission):
    """
    Grants access if the user is the task creator or board owner.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Task):
            return obj.created_by == request.user or obj.board.owner == request.user
        return False


class IsCommentAuthor(BasePermission):
    """
    Grants access if the user is the author of the comment.
    """
    def has_object_permission(self, request, view, obj):
        if isinstance(obj, Comment):
            return obj.author == request.user
        return False