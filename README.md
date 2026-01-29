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
      # Django KanMind API

      This repository contains the backend API for KanMind, built with Django and Django REST Framework.

      ## Technologies
      - Django
      - Django REST Framework (DRF)

      ## Quick start
      1. Clone the repository:

         ```bash
         git clone <repo-url>
         cd Backend---KanMind
         ```

      2. Create and activate a virtual environment:

         ```bash
         python -m venv .venv
         # Windows
         .venv\Scripts\activate
         # macOS / Linux
         source .venv/bin/activate
         ```

      3. Install dependencies:

         ```bash
         pip install -r requirements.txt
         ```

      4. Apply migrations and create the database (SQLite is used for local development):

         ```bash
         python manage.py makemigrations
         python manage.py migrate
         ```

      5. Create a superuser for admin access (optional):

         ```bash
         python manage.py createsuperuser
         ```

      6. Run the development server:

         ```bash
         python manage.py runserver
         ```

      ## Tests & Coverage
      Run tests with coverage locally:

      ```bash
      pip install pytest pytest-cov
      pytest --maxfail=1 --disable-warnings -q --cov=. --cov-fail-under=95
      ```

      The project includes a GitHub Actions workflow that runs the test suite and enforces a minimum coverage of 95%.

      ## API Endpoints
      - Authentication: `/api/registration/`, `/api/login/`
      - Boards: `/api/boards/`, `/api/boards/{id}/`
      - Tasks: `/api/tasks/`, `/api/tasks/{id}/`, `/api/tasks/assigned-to-me/`, `/api/tasks/reviewing/`
      - Comments: `/api/tasks/{task_id}/comments/`, `/api/tasks/{task_id}/comments/{comment_id}/`
      - Email check: `/api/email-check/?email=...`

      ## Notes
      - Token authentication (DRF token) is configured in `core/settings.py`.
      - Admin panel: `/admin/`.

      ## DoD / Remaining Requirements
      - Remove committed database: Done (should be removed from Git history if pushed to remote).
      - README is now in English and documents setup and tests.

      If you want, I can also add formatting (black) and linting (flake8) configuration, or set up pre-commit hooks.