# Django KanMin API

Welcome to the backend of the KanMind project! This Django-based API provides the server logic for an application. It allows managing boards, tasks and users through RESTful endpoints.

## Technologies
- Django: Web framework for Python
- Django REST Framework: For API development
- SQLite: Database (default for local development)

## Quick start
1. Clone the repository and navigate to the folder:
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

4. Apply migrations: <br>
      Erstellen sie einen ordner unter **./board_app/** namens **```migrations```**. <br>
      Und anschliessend eine datei unter **./board_app/migrations/** namens **```__init__.py```**

      ```
      python manage.py makemigrations
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