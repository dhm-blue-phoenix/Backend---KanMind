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

2. For the setup script from:
      ### Under Windwos (Powershell)
      ```
      .setup/init.ps1
      ```

      ### On Linux
      ```
      chmod +x ./setup/init.sh
      .setup/init.sh
      ```

      ### Optional Parameters
      Both parameters can also be specified. <br>
      Example: file ``` --superuser --code --run ```

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

      ## API Endpoints
      - Authentication: `/api/registration/`, `/api/login/`
      - Boards: `/api/boards/`, `/api/boards/{id}/`
      - Tasks: `/api/tasks/`, `/api/tasks/{id}/`, `/api/tasks/assigned-to-me/`, `/api/tasks/reviewing/`
      - Comments: `/api/tasks/{task_id}/comments/`, `/api/tasks/{task_id}/comments/{comment_id}/`
      - Email check: `/api/email-check/?email=...`