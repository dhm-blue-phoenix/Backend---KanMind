# Django REST Framework
from django.urls import path

# Local imports
from .views import (
    EmailCheckView, BoardListCreateView, BoardDetailView, TaskCreateView,
    AssignedToMeTasksView, ReviewingTasksView, TaskDetailView, TaskCommentsListCreateView,
    TaskCommentDeleteView
)

urlpatterns = [
    path('email-check/', EmailCheckView.as_view(), name='email-check'),

    path('boards/', BoardListCreateView.as_view(), name='board-list-create'),
    path('boards/<int:board_id>/', BoardDetailView.as_view(), name='board-detail'),

    path('tasks/', TaskCreateView.as_view(), name='task-create'),
    path('tasks/assigned-to-me/', AssignedToMeTasksView.as_view(), name='tasks-assigned-to-me'),
    path('tasks/reviewing/', ReviewingTasksView.as_view(), name='tasks-reviewing'),
    path('tasks/<int:task_id>/', TaskDetailView.as_view(), name='task-detail'),
    path('tasks/<int:task_id>/comments/', TaskCommentsListCreateView.as_view(), name='task-comments-list-create'),
    path('tasks/<int:task_id>/comments/<int:comment_id>/', TaskCommentDeleteView.as_view(), name='task-comment-delete'),
]