# Django KanMin API

<br>

## Installation
1. Clone the repository:
      ```
      git clone https://github.com/dhm-blue-phoenix/Backend---KanMind.git
      cd Backend---KanMind
      ```

2. Create and activate a virtual environment:
      ```
      python -m venv venv
      ```

      **Linux**
      ```
      . venv/bin/activate
      ```

      **Windows**
      ```
      venv\Scripts\activate
      ```

3. Install dependencies:
      ```
      pip install -r requirements.txt
      ```

4. Apply migrations:
      ```
      python manage.py makemigrations
      python manage.py makemigrations board_app
      python manage.py migrate
      ```

5. Create a superuser (for admin):
      ```
      python manage.py createsuperuser
      ```

6. Run the server:
      ```
      python manage.py runserver
      ```

## API Endpoints
- Authentication: <br>
      `/api/registration/`, <br>
      `/api/login/`

- Boards: <br>
      `/api/boards/`, <br>
      `/api/boards/{id}/`

- Tasks: <br>
      `/api/tasks/`, <br>
      `/api/tasks/{id}/`, <br>
      `/api/tasks/assigned-to-me/`, <br>
      `/api/tasks/reviewing/`

- Comments: <br>
      `/api/tasks/{task_id}/comments/`, <br>
      `/api/tasks/{task_id}/comments/{comment_id}/`

- Other: <br>
      `/api/email-check/?email=...`

## Notes
- Uses Token Authentication.
- Admin panel available at `/admin/`.