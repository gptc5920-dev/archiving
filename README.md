# JRMSU Registrar Archive

A Django registrar archive for student records. Registrar staff can manage student profiles in the Django admin and attach archived documents such as PDFs, transcripts, certificates, and scanned image files.

It also includes a small Django REST Framework API for user account CRUD operations. The custom `User` model is based on `AbstractUser`, with `email` as the login identifier.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\python -m pip install -r requirements.txt
.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py createsuperuser
.\.venv\Scripts\python manage.py runserver
```

The Django admin UI uses [Unfold](https://unfoldadmin.com/) and is available at `/admin/`. It includes a branded sidebar, command search, account badges, user-list tabs, and dashboard user stats.

## Registrar Archive

The admin includes:

| Model | Description |
| --- | --- |
| `College` | College catalog with code, name, active status, and links to filtered courses/students |
| `Course` | Course catalog with BS/BA template, code, name, college, duration, and links to filtered students |
| `Student` | Student identity, college, course, academic status, contact details, and archive notes |
| `StudentDocument` | Uploaded registrar files linked to a student record |

Document uploads allow `pdf`, `jpg`, `jpeg`, `png`, and `webp` files. Uploaded files are stored under `media/student-records/{student-number}/` during local development.

The College and Course admin modules link directly to paginated Course and Student lists. The Student list can be filtered by course, college, year level, and status for faster retrieval.

Student and document admin pages include an embedded viewer for archived PDFs and images, so registrar staff can review every document attached to a student record without leaving the student page.

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `POST` | `/api/accounts/` | Public | Create an account |
| `GET` | `/api/accounts/` | Admin | List accounts |
| `GET` | `/api/accounts/users/` | Admin | Get list of users |
| `GET` | `/api/accounts/{id}/` | Admin or same user | Retrieve an account |
| `PUT` | `/api/accounts/{id}/` | Admin or same user | Replace account fields |
| `PATCH` | `/api/accounts/{id}/` | Admin or same user | Update account fields, including password |
| `DELETE` | `/api/accounts/{id}/` | Admin or same user | Delete an account |

## Create User

```http
POST /api/accounts/
Content-Type: application/json

{
  "email": "new@example.com",
  "username": "newuser",
  "password": "new-secret-123",
  "first_name": "New",
  "last_name": "User"
}
```

Passwords are write-only and are hashed before storage.

Example response:

```json
{
  "id": 1,
  "email": "new@example.com",
  "username": "newuser",
  "first_name": "New",
  "last_name": "User"
}
```

## Get List of Users

```http
GET /api/accounts/users/
Authorization: Basic admin@example.com:admin-secret-123
```

Example response:

```json
[
  {
    "id": 1,
    "email": "admin@example.com",
    "username": "admin",
    "first_name": "",
    "last_name": "",
    "is_active": true,
    "is_staff": true,
    "date_joined": "2026-04-25T12:00:00Z"
  }
]
```

## Update Password

```http
PATCH /api/accounts/1/
Content-Type: application/json

{
  "password": "updated-secret-123"
}
```

## Tests

```powershell
.\.venv\Scripts\python manage.py test
```
