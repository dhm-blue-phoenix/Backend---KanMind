# Django KanMin API

Welcome to the backend of the KanMind project! This Django-based API provides the server logic for an application. It allows managing boards, tasks and users through RESTful endpoints.

## Requirements
**Python:** 3.12 (the project requires Python 3.12 or higher for local development).
Check your Python version: <br>

System Python check:
```
python --version
```

## Quick start
1. Clone the repository and navigate to the folder:
      ```
      git clone https://github.com/dhm-blue-phoenix/Backend---KanMind.git
      cd Backend---KanMind
      ```

## Setting up with setup file
2. For the setup on:
      ### Windwos (Powershell)
      ```
      .setup/init.ps1
      ```

      ### Linux
      ```
      chmod +x .setup/init.sh
      .setup/init.sh
      ```

      ### Optional Parameters
      Both parameters can also be specified. <br>
      Example: .setup/init ``` --superuser --code --run ```

      Set up setup with superuser <br>
      ```
      --superuser
      ```
      Start Code Editor (VScode) with <br>
      ```
      --code
      ```
      Start server right in the console <br>
      ```
      --run
      ```

## Manual setup without setup file
2. Create and activate a virtual environment:
      ```
      python -m venv .venv
      ```

      ### On Windows
      ```
      .venv\Scripts\activate
      ```

      ### On Linux
      ```
      . .venv/bin/activate
      ```

3. Install dependencies:
      ```
      pip install -r requirements.txt
      ```

4. Apply migrations and create the database (SQLite is used for local development): <br>

      Create a folder under **./board_app/** named **```migrations```**. <br>
      And then a file under **./board_app/migrations/** called **```__init__.py```** <br>

      ```
      python manage.py makemigrations
      python manage.py migrate
      ```

5. Create a superuser for admin access (optional):
      ```
      python manage.py createsuperuser
      ```

6. Run the development server:
      ```
      python manage.py runserver
      ```

## Vscode (finds the workspace at: __".setup/"__)
The server can also be started in vscode via: 
- Start Django server with debugger (F5) <br>
- Django run server per Task (STRG+SHIFT+B) <br> <br>
In workspace, the task is set to autostart but can only be used via an extension: <br>
Name: __Auto Run Command__ <br>
Publisher: __Augustin Riedinger__

## API Endpoints
- Authentication: `/api/registration/`, `/api/login/`
- Boards: `/api/boards/`, `/api/boards/{id}/`
- Tasks: `/api/tasks/`, `/api/tasks/{id}/`, `/api/tasks/assigned-to-me/`, `/api/tasks/reviewing/`
- Comments: `/api/tasks/{task_id}/comments/`, `/api/tasks/{task_id}/comments/{comment_id}/`
- Email check: `/api/email-check/?email=...`