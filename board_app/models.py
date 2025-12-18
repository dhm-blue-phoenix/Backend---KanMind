# Django
from django.db import models
from django.contrib.auth.models import User

STATUS_CHOICES = [
    ('to-do', 'To Do'),
    ('in-progress', 'In Progress'),
    ('review', 'Review'),
    ('done', 'Done'),
]

PRIORITY_CHOICES = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
]

class Board(models.Model):
    """
    Model for boards.
    Has title, owner, and many-to-many members.
    """
    title = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_boards')
    members = models.ManyToManyField(User, related_name='boards', blank=True)

    class Meta:
        verbose_name = 'Board'
        verbose_name_plural = 'Boards'
        ordering = ['-id']

    def __str__(self):
        return self.title

    def member_count(self):
        return self.members.count()

    def task_count(self):
        return self.tasks.count()

    def tasks_to_do_count(self):
        return self.tasks.filter(status='to-do').count()

    def tasks_high_prio_count(self):
        return self.tasks.filter(priority='high').count()


class Task(models.Model):
    """
    Model for tasks.
    Belongs to a board, has status, priority, assignee, reviewer.
    """
    board = models.ForeignKey(Board, on_delete=models.CASCADE, related_name='tasks')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_tasks')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='to-do')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    assignee = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tasks')
    reviewer = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='reviewing_tasks')
    due_date = models.DateField(null=True, blank=True)

    class Meta:
        verbose_name = 'Task'
        verbose_name_plural = 'Tasks'
        ordering = ['-id']

    def __str__(self):
        return self.title

    def comments_count(self):
        return self.comments.count()


class Comment(models.Model):
    """
    Model for comments.
    Belongs to a task, has author and content.
    """
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Comment'
        verbose_name_plural = 'Comments'
        ordering = ['created_at']

    def __str__(self):
        return f"Comment by {self.author} on {self.task}"