# Django
from django.contrib import admin

# Local imports
from .models import Board, Task, Comment

admin.site.register(Board)
admin.site.register(Task)
admin.site.register(Comment)