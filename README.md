# Django Kanban API

This is a Django-based API for managing boards, tasks, and comments, with user authentication.

## Prerequisites
- Python 3.10+
- Virtual environment (recommended)

## Installation
1. Clone the repository:
      git clone <repo-url>
      cd <repo-dir>

2. Create and activate a virtual environment:
      python -m venv venv

      # Linux Arch
      source venv/bin/activate
      or
      source venv/bin/activate.fish

      # On Windows:
      venv\Scripts\activate

3. Install dependencies:
      pip install -r requirements.txt

4. Apply migrations:
      python manage.py makemigrations
      python manage.py makemigrations board_app
      python manage.py migrate

5. Create a superuser (for admin):
      python manage.py createsuperuser

6. Run the server:
      python manage.py runserver

## API Endpoints
- Authentication:
      `/api/registration/`,
      `/api/login/`
- Boards:
      `/api/boards/`,
      `/api/boards/{id}/`
- Tasks:
      `/api/tasks/`,
      `/api/tasks/{id}/`,
      `/api/tasks/assigned-to-me/`,
      `/api/tasks/reviewing/`
- Comments:
      `/api/tasks/{task_id}/comments/`,
      `/api/tasks/{task_id}/comments/{comment_id}/`
- Other:
      `/api/email-check/?email=...`

## Notes
- Uses Token Authentication.
- Admin panel available at `/admin/`.