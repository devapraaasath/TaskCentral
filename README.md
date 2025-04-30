<<<<<<< HEAD
# TaskCentral API

A Django REST Framework-based API for enterprise project coordination with role-based authorization.

## Overview

TaskCentral delivers a robust API for managing projects and tasks within a structured permission framework:

- **Administrators** (Level 1): Complete system access
- **Managers** (Level 2): Task oversight and assignment
- **Team Members** (Level 3): Assigned task management

## Technology Stack

- **Backend**: Django 5.0 with Django REST Framework
- **Authentication**: JSON Web Token (JWT) via SimpleJWT
- **Data Storage**: PostgreSQL
- **API Documentation**: Swagger/OpenAPI through drf-spectacular
- **Testing**: Built-in Django test framework

## Key Capabilities

- **Secure Authentication** using JWT tokens
- **Role-Based Authorization**: 
  - Administrators: Full system control
  - Managers: Task oversight capabilities
  - Team Members: Personal task updates
- **Project Management**: 
  - Complete CRUD operations
  - Metadata and description handling
  - Timeline scheduling
- **Task Processing**: 
  - CRUD functionality
  - Status tracking (Pending, In Progress, Completed)
  - Priority levels (Low, Standard, High)
  - Deadline management
- **Resource Allocation**: Assign tasks to specific team members
- **Advanced Filtering**:
  - Tasks by project, status, priority, deadline
  - Projects by title, creator, timeline
- **Paged Results**: All listing endpoints (10 items per page)

## Design Decisions

### 1. Security & Authentication
- **Token-based Authentication**: Implemented with djangorestframework-simplejwt for secure, stateless sessions
- **Email Authentication**: Email-based account system rather than username
- **Permission Framework**: Custom permission classes for granular access control

### 2. API Architecture
- **RESTful Design**: Resource-based URL structure with consistent patterns
- **Serialization Layer**: Comprehensive validation and data transformation
- **Generic View Structure**: Leveraging DRF class-based views
- **Interactive Documentation**: Auto-generated API documentation

### 3. Data Structure
- **PostgreSQL Database**: Selected for reliability and complex query support
- **Relational Model**: Well-defined relationships between User, Project, and Task entities
- **Data Integrity**: Model-level validation and constraints

### 4. Structure & Organization
- **Modular Architecture**: Separated components for maintainability
- **Reusable Components**: Shared permission classes and serializers
- **Test Coverage**: Comprehensive test suite

## Setup Guide

### Prerequisites

- Python 3.8+
- PostgreSQL

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Unix/MacOS
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure PostgreSQL in `TaskCentral/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': 'Managment',  # Database name
           'USER': 'postgres',   # Database user
           'PASSWORD': '2311',   # Database password
           'HOST': 'localhost',
           'PORT': '5432'
       }
   }
   ```

5. Apply migrations:
   ```bash
   python manage.py migrate
   ```

6. Create an administrator account:
   ```bash
   python manage.py createsuperuser
   ```

7. Launch the server:
   ```bash
   python manage.py runserver
   ```

8. Access the API at http://127.0.0.1:8000/
9. Access documentation at http://127.0.0.1:8000/swagger/

## Authentication

The API employs JWT tokens for authentication:

- **Token Format**: `JWT your_token_here` (uses 'JWT' prefix)
- **Token Lifespan**: Access tokens valid for 25 minutes
- **Authentication Header**: `Authorization: JWT your_token_here`

## API Endpoints

### Authentication

- `POST /register/`: Create a new account
- `POST /login/`: Authenticate and receive JWT tokens
- `POST /token/refresh/`: Renew an expired token
- `POST /token/obtain/`: Direct token acquisition

### User Management

- `GET /users/`: List all users (administrators only)
- `PUT /users/{email}/role/`: Update user permissions (administrators only)

### Projects

- `GET /projects/`: List projects with filtering
- `POST /projects/`: Create a project (administrators only)
- `GET /projects/{id}/`: View project details
- `PUT/PATCH /projects/{id}/`: Update a project (administrators only)
- `DELETE /projects/{id}/`: Remove a project (administrators only)

### Tasks

- `GET /tasks/`: List tasks with filtering
- `POST /tasks/`: Create a new task
- `GET /tasks/{id}/`: View task details
- `PUT/PATCH /tasks/{id}/`: Update a task (permission-based)
- `DELETE /tasks/{id}/`: Remove a task (administrators & managers)
- `PUT /tasks/{id}/assign/`: Assign a task to a team member

## Filtering Examples

- **Tasks by project**: `/tasks/?project=1`
- **Tasks by status**: `/tasks/?status=In Progress`
- **Tasks by priority**: `/tasks/?priority=High`
- **Tasks by due date**: `/tasks/?due_date=2025-05-15`
- **Projects by title**: `/projects/?title=Frontend`
- **Combined filters**: `/tasks/?project=1&status=In Progress&priority=High`

## Pagination

All listing endpoints have 10-item pagination:
- `/tasks/?page=2`
- `/projects/?page=3`

## Role-Based Permissions

### Administrator (role=1):
- Complete CRUD access to all projects and tasks
- User role management
- Task assignment capabilities

### Manager (role=2):
- View-only access to projects
- Create, update and delete tasks
- Assign tasks to team members

### Team Member (role=3):
- View assigned tasks
- Update status of assigned tasks
- View projects containing assigned tasks

## Testing

The project includes comprehensive testing:

```bash
python manage.py test user_board
```

Test suite covers:
- Account creation and authentication
- Role-based permission enforcement
- Project management operations
- Task handling and assignment
- Filtering and pagination
=======
# TaskCentral
>>>>>>> 8918aabaede0ed96455d2d184cd2a147194d8f38
