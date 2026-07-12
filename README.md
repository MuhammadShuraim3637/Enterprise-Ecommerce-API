# Enterprise E-Commerce Backend (FastAPI)

A production-style, modular e-commerce backend built with **FastAPI**, **SQLAlchemy**, and **JWT-based authentication**. This project was built to demonstrate real-world backend engineering practices — clean architecture, layered service design, security-first authentication, real-time features via WebSockets, and a disciplined automated test suite.

---

## 🚀 Features

- **Authentication & Authorization**
  - JWT access & refresh token flow
  - Email verification flow
  - Forgot / reset password flow
  - Role-based access control (regular users vs. admin/superuser)
  - Secure password hashing with `bcrypt`

- **Product Catalog**
  - Full CRUD for products and categories
  - Advanced search, filtering (category, price range), sorting, and pagination
  - Product image uploads
  - Auto-generated SEO-friendly slugs

- **Shopping Cart**
  - Add / update / remove items
  - Stock-aware quantity validation
  - Cart summary and clearing

- **Orders & Stock Management**
  - Order creation with automatic stock deduction
  - Order cancellation with stock rollback
  - Order status lifecycle (pending → shipped → delivered, etc.)

- **Payments**
  - Payment processing flow tied to orders

- **Reviews**
  - Product review submission and retrieval

- **Real-Time Updates (WebSockets)**
  - Live support chat over WebSocket
  - Real-time order status broadcast to connected clients
  - Per-user multi-device connection tracking

- **Users & Admin**
  - User profile management
  - Admin-only endpoints for managing all users

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| Database | PostgreSQL |
| ORM | SQLAlchemy |
| Migrations | Alembic |
| Validation | Pydantic v2 |
| Auth | JWT (`python-jose`), `bcrypt` |
| Testing | Pytest, pytest-cov, FastAPI TestClient |
| Real-time | Starlette WebSockets |
| Language | Python 3.14 |

---

## 📂 Project Structure

```
app/
├── api/
│   └── v1/
│       ├── api.py                  # Central API router (aggregates all endpoint routers)
│       └── endpoints/
│           ├── auth.py             # Register, login, verify, forgot/reset password, refresh, logout
│           ├── users.py            # User profile & admin user management
│           ├── category_router.py  # Category CRUD
│           ├── product_router.py   # Product CRUD
│           ├── image.py            # Product image upload
│           ├── review_router.py    # Product reviews
│           ├── order_router.py     # Order creation & management
│           ├── payment_router.py   # Payment processing
│           ├── cart_router.py      # Shopping cart operations
│           └── websocket_router.py # Real-time chat & order updates
│
├── core/
│   ├── config.py                   # App settings (env-based)
│   ├── database.py                 # DB session & engine setup
│   ├── security.py                 # Password hashing & JWT helpers
│   └── logger.py                   # Logging configuration
│
├── dependencies/
│   └── auth.py                     # get_current_user / get_admin_user dependencies
│
├── models/                         # SQLAlchemy ORM models
│   ├── user.py
│   ├── product.py
│   ├── category.py
│   ├── cart.py
│   ├── order.py
│   ├── order_item.py
│   ├── payment.py
│   └── review.py
│
├── repositories/
│   └── user_repository.py          # Data-access layer for User
│
├── schemas/                        # Pydantic request/response models
│
├── services/                       # Business logic layer
│   ├── auth_service.py
│   ├── product_service.py
│   ├── cart_service.py
│   ├── category_service.py
│   ├── order_service.py
│   ├── payment_service.py
│   ├── review_service.py
│   ├── user_service.py
│   ├── email_service.py
│   └── websocket_manager.py
│
├── utils/
│   ├── token.py                    # Random token & JWT generation helpers
│   ├── email.py
│   ├── payment_gateway.py
│   └── upload.py
│
└── main.py                         # FastAPI app entrypoint

tests/                              # Full automated test suite (see below)
```

**Design pattern:** Router → Service → Repository/ORM. Routers stay thin (HTTP concerns only), services own business logic, and the repository layer abstracts direct DB access for the User model.

---

## ✅ Test Suite & Coverage

This project has a strong emphasis on **automated testing**, built incrementally and audited module-by-module to close coverage gaps rather than chasing a number blindly.

```
88 tests passed
Overall coverage: 93%
```

### Coverage by critical module

| Module | Coverage | Notes |
|---|---|---|
| `auth_service.py` | **100%** | Register, login, verify email, forgot/reset password, refresh, logout — all success and failure paths |
| `core/security.py` | **100%** | Password hashing, JWT access/refresh token creation, corrupt-hash handling |
| `product_service.py` | **100%** | Search, filter, sort, pagination, create, update, image upload, slug generation |
| `websocket_manager.py` | **100%** | Connect/disconnect, personal messaging, broadcast, stale-connection handling |
| `auth.py` (endpoints) | **100%** | Full endpoint-level integration coverage |
| `users.py`, `cart_router.py`, `category_router.py` | **100%** | Full CRUD and role-based access coverage |
| `order_service.py` | 92% | Stock deduction, rollback, status transitions |
| `cart_service.py` | 91% | Add/update/remove/clear cart flows |
| `payment_service.py` | 82% | Payment processing flow |
| `websocket_router.py` | 68% | Auth handshake and token validation fully covered; live chat loop partially covered (thread-based execution) |

### Testing approach

- **Integration tests** (`tests/test_*.py`) use FastAPI's `TestClient` to exercise full HTTP request/response flows against a test database.
- **Service-level unit tests** (e.g. `test_product_service.py`, `test_security.py`, `test_websocket_manager.py`) bypass the HTTP layer entirely to test business logic in isolation — faster and more precise for edge cases.
- **Mocked WebSocket testing**: a lightweight `FakeWebSocket` class is used to unit-test `WebSocketManager` without needing a real socket connection.
- Deliberate focus on **negative paths and edge cases**, not just happy paths: wrong passwords, expired/invalid tokens, inactive/unverified accounts, out-of-stock scenarios, non-existent resources, and malformed input.

### Running the tests

```bash
# Run the full suite with coverage report
pytest

# Run a specific test file
pytest tests/test_auth.py -v

# Run with verbose output
pytest -v
```

Coverage configuration lives in `.coveragerc` (enables `concurrency = thread` so background-thread execution, such as WebSocket connections spawned by `TestClient`, is correctly tracked).

---

## 🔐 Security Notes

- Passwords are hashed using `bcrypt` — never stored or logged in plaintext.
- Access tokens are short-lived; refresh tokens are used to re-issue access tokens without re-authentication.
- Email verification is required before a user can access protected resources (`403 Forbidden` otherwise).
- Admin-only routes are protected via a dedicated `get_admin_user` dependency, tested against regular-user access attempts.
- `forgot-password` intentionally returns a generic `200 OK` regardless of whether the email exists, to avoid leaking account existence.

---

## ⚙️ Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL (running locally or accessible remotely)
- A virtual environment tool (`venv`, `poetry`, etc.)

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd enterprise-ecommerce

# Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### Environment Variables

Create a `.env` file in the project root with (at minimum):

```
SECRET_KEY=your-secret-key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
DATABASE_URL=postgresql://<user>:<password>@localhost:5432/<db_name>
```

Make sure the PostgreSQL database referenced above already exists (`CREATE DATABASE <db_name>;`) before running migrations.

### Database Migrations (Alembic)

This project uses **Alembic** for schema migrations against PostgreSQL. After setting up your `.env`, run migrations before starting the app for the first time:

```bash
# Check current migration state
alembic current

# Apply all pending migrations
alembic upgrade head
```

If you add or change a model, generate a new migration:

```bash
alembic revision --autogenerate -m "describe your change"
alembic upgrade head
```

> **Note:** `alembic/env.py` must import every SQLAlchemy model (not just `User`) so that `Base.metadata` is aware of all tables. If a model isn't imported there, `--autogenerate` will silently skip its table — this project hit exactly that issue during development (see commit history / lessons learned).

### Running the App

```bash
uvicorn app.main:app --reload
```

- API docs (Swagger UI): `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

---

## 🖥️ Demo Dashboard (Next.js)

A minimal single-file Next.js dashboard (`page.tsx`) is included as a companion demo — it exercises the live API from the browser: signup/login, product search & filtering, and a local cart preview. It's a thin API console, not a full storefront, meant to visually demonstrate the backend working end-to-end.

```bash
# In a separate Next.js project
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1  # add to .env.local
npm run dev
```

Make sure the FastAPI server is running first (`uvicorn app.main:app --reload`) — the dashboard shows a live connection status indicator that pings `/health`.

---

## 📌 Roadmap / Future Improvements

- Expose `get_products_advanced` (search/filter/sort/pagination) via a dedicated API endpoint — currently service-level only.
- Increase `websocket_router.py` coverage for the live chat message loop.
- Add structured logging via `core/logger.py`.
- Rate limiting on auth endpoints (login, forgot-password).

---

## 👤 Author

Built by Muhammad Shuraim as a backend engineering portfolio project, demonstrating FastAPI architecture, JWT authentication, real-time systems, and disciplined test-driven development.
