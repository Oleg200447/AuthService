# Auth Service

Asynchronous authentication service built with FastAPI, supporting Google OAuth and system account authentication.

## Features

- **Google OAuth 2.0** - User authentication via Google
- **System Accounts** - Service-to-service authentication
- **JWT Tokens** - Secure token-based authentication
- **Async/Await** - Fully asynchronous implementation
- **PostgreSQL** - Async database operations with SQLAlchemy 2.0
- **Kafka Integration** - Event publishing for new user registrations
- **Docker Support** - Containerized deployment
- **Alembic Migrations** - Database version control
- **OpenAPI/Swagger** - Auto-generated API documentation

## Architecture

```
AuthService/
├── app/
│   ├── api/              # API endpoints
│   ├── core/             # Core functionality (security, OAuth, Kafka)
│   ├── db/               # Database session management
│   ├── models/           # Database and Pydantic models
│   ├── config.py         # Configuration management
│   ├── exceptions.py     # Custom exceptions
│   └── main.py           # Application entry point
├── alembic/              # Database migrations
├── Dockerfile
├── docker-compose.yml
└── requirements.txt
```

## Prerequisites

- Python 3.11+
- PostgreSQL 15
- Kafka (optional, for new user events)
- Docker & Docker Compose (for containerized deployment)

## Setup

### 1. Environment Configuration

Copy `.env.example` to `.env` and fill in your actual values:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Google OAuth credentials (from Google Cloud Console)
- JWT secret key
- System account secret keys
- Kafka broker address
- Database connection string

### 2. Database Setup

The database should be running in Docker (as per your setup):

```bash
docker run -d \
  --network test_network \
  --name database_auth_service \
  -e POSTGRES_USER=admin \
  -e POSTGRES_PASSWORD=519121 \
  -e POSTGRES_DB=auth_db \
  -p 5433:5432 \
  -v pgdata:/var/lib/postgresql/data \
  postgres:15
```

**Note**: PostgreSQL runs on port 5432 internally, but you mapped it to 5433 on the host. Make sure your `DATABASE_URL` reflects this:
```
DATABASE_URL=postgresql+asyncpg://admin:519121@database_auth_service:5432/auth_db
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Database Migrations

```bash
# Apply migrations to create database tables
alembic upgrade head
```

This creates all the necessary database tables (users, system_accounts, pre_auth_sessions).

### 5. Seed System Accounts

After running migrations, you need to seed the system accounts:

```bash
# Run the seeding script to create system accounts
python scripts/seed_system_accounts.py
```

This script:
- Creates 5 system accounts (system_1 through system_5)
- Uses Argon2 for hashing secret keys (no 72-byte limit like bcrypt)
- Is idempotent - can be run multiple times safely
- Skips existing accounts automatically

**Note**: Make sure your `.env` file contains all required `SYSTEM_X_SECRET` values before running the seeding script.

### 6. Run the Service

#### Development Mode:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode with Docker:
```bash
docker-compose up -d
```

## API Endpoints

### Health Check
- `GET /` - Root endpoint
- `GET /health` - Health check

### Google OAuth (Users)
- `POST /auth/oauth/google` - Google OAuth callback

### Onboarding
- `POST /auth/onboarding/username` - Set username during onboarding
- `GET /auth/onboarding/state` - Check onboarding state

### System Accounts
- `POST /auth/system/login` - System account login

### Documentation
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc UI

## API Usage Examples

### 1. Google OAuth Login

**Request:**
```http
POST /auth/oauth/google
Content-Type: application/json

{
  "code": "4/0AY0e-g6aBcdef12345XYZ",
  "code_verifier": "random_pkce_string"
}
```

**Response (Existing User):**
```json
{
  "status": "AUTHENTICATED",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900,
  "user": {
    "sub": "uuid-user-123",
    "nickname": "ivan_petrov",
    "role": "user",
    "email": "user@gmail.com",
    "name": "Ivan Petrov"
  }
}
```

**Response (New User):**
```json
{
  "status": "ONBOARDING_REQUIRED",
  "pre_auth_token": "uuid-1234",
  "expires_in": 600,
  "next_step": "SET_USERNAME",
  "user_info": {
    "email": "user@gmail.com",
    "name": "Ivan Petrov"
  }
}
```

### 2. Set Username (Onboarding)

**Request:**
```http
POST /auth/onboarding/username
Authorization: PreAuth uuid-1234
Content-Type: application/json

{
  "username": "ivan_petrov"
}
```

**Response:**
```json
{
  "status": "AUTHENTICATED",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900,
  "user": {
    "sub": "uuid-user-123",
    "nickname": "ivan_petrov",
    "role": "user",
    "email": "user@gmail.com",
    "name": "Ivan Petrov"
  }
}
```

### 3. System Account Login

**Request:**
```http
POST /auth/system/login
Content-Type: application/json

{
  "username": "system_1",
  "secret_key": "your-secret-key-here"
}
```

**Response:**
```json
{
  "status": "AUTHENTICATED",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 3600,
  "user": {
    "sub": "uuid-system-1",
    "nickname": "system_1",
    "role": "system"
  }
}
```

## JWT Token Structure

```json
{
  "sub": "uuid",
  "nickname": "username",
  "role": "user | system",
  "exp": 1700003600
}
```

## Kafka Events

When a new user completes onboarding, a message is published to the `new_users` topic:

```json
{
  "id": "uuid-user-123",
  "username": "ivan_petrov",
  "created_at": "2026-01-04T04:59:00.123456+00:00"
}
```

## Database Schema

### Users Table
```sql
CREATE TABLE users (
  id          UUID PRIMARY KEY,
  username    TEXT NOT NULL UNIQUE,
  google_sub  TEXT NOT NULL UNIQUE,
  email       TEXT,
  name        TEXT,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### System Accounts Table
```sql
CREATE TABLE system_accounts (
  id               UUID PRIMARY KEY,
  username         TEXT NOT NULL UNIQUE,
  secret_key_hash  TEXT NOT NULL,
  active           BOOLEAN NOT NULL DEFAULT true,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

### Pre-Auth Sessions Table
```sql
CREATE TABLE pre_auth_sessions (
  id          UUID PRIMARY KEY,
  google_sub  TEXT NOT NULL UNIQUE,
  email       TEXT,
  name        TEXT,
  expires_at  TIMESTAMPTZ NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

## Error Codes

- `USERNAME_TAKEN` - Username is already in use
- `INVALID_CREDENTIALS` - Invalid username or password
- `TOKEN_EXPIRED` - Pre-auth token has expired
- `TOKEN_NOT_FOUND` - Pre-auth token not found
- `OAUTH_FAILED` - Google OAuth authentication failed
- `INTERNAL_SERVER_ERROR` - Unexpected server error

## Security Notes

⚠️ **Important**: The current Google ID token verification is insecure for production. Implement proper JWT verification with Google's public keys before deploying to production.

## Development

### Run Alembic Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

### Logs
The service uses structured logging with the following levels:
- INFO - General operational messages
- WARNING - Warning messages
- ERROR - Error messages

Configure log level in `.env`:
```
LOG_LEVEL=INFO
```

## License

MIT License
