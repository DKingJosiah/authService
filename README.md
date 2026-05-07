# Auth Service

A **FastAPI** based authentication microservice providing secure user registration, login, password management, and application integration.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Service](#running-the-service)
  - [Database Migrations](#database-migrations)
- [API Overview](#api-overview)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **User Registration & Email Verification**
- **JWT based Authentication**
- **Password Reset & Change**
- **Application Management** – support for multiple client applications
- **Social Authentication (Google/Facebook)** – extensible for future providers
- **Rate Limiting** with `slowapi`
- **Database migrations** via Alembic
- **Dockerized** for easy deployment

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Web Framework** | FastAPI |
| **Database ORM** | SQLAlchemy |
| **Migrations** | Alembic |
| **Authentication** | PyJWT |
| **Email** | `aiosmtplib` (or any SMTP provider) |
| **Rate Limiting** | slowapi |
| **Containerisation** | Docker & Docker‑Compose |
| **Testing** | pytest |
| **Python Version** | 3.11 |

---

## Getting Started

### Prerequisites

- **Python 3.11+**
- **Docker & Docker‑Compose** (optional, for containerised run)
- **Git**
- **Virtual environment** (recommended)

### Installation

```bash
# Clone the repository (if not already done)
git clone https://github.com/DKingJosiah/authService.git
cd auth-service

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# .\venv\Scripts\activate  # Windows PowerShell

# Install dependencies
pip install -r requirements.txt
```

### Running the Service

#### Locally (development)

```bash
# Start the FastAPI server
uvicorn app.main:app --reload
```

Open your browser at `http://127.0.0.1:8000/docs` to explore the automatically generated OpenAPI documentation.

#### With Docker

```bash
docker-compose up --build
```

The service will be available at `http://localhost:8000`.

### Database Migrations

```bash
# Initialise the database (creates tables)
alembic upgrade head
```

If you modify models, generate a new migration:

```bash
alembic revision --autogenerate -m "Your description"
```

---

## API Overview

The API is versioned under `/api/v1/` (adjust as needed). Key endpoints include:

- `POST /auth/register` – Register a new user and send verification email.
- `POST /auth/login` – Obtain JWT access/refresh tokens.
- `POST /auth/refresh` – Refresh access token.
- `POST /auth/password/forgot` – Request password reset email.
- `POST /auth/password/reset` – Reset password using token.
- `GET /applications/` – List registered client applications.
- `POST /applications/` – Register a new client application.

For a full list, refer to the OpenAPI docs (`/docs`).

---

## Testing

```bash
# Run the test suite
pytest
```

Make sure the test database URL is configured in `app/config.py` or via the `TEST_DATABASE_URL` environment variable.

---

## Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature/awesome-feature`).
3. Commit your changes with clear messages.
4. Push to your fork and open a Pull Request.
5. Ensure all tests pass and code follows the existing style.

---

## License

This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

*Happy coding!*
