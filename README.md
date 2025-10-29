# Restaurant Management System — Django backend (production-ready, typed, well-tested)

A complete, production-minded Django REST backend for restaurant operations. Manage menus, inventory, tables, reservations, and orders with role-based access, JWT authentication, and automated tests that keep critical business rules verifiable.

## Features

- **Typed Django models, serializers, views, and services** for clarity and maintainability.
- **Full REST API** powered by Django REST Framework with pagination and standardized exceptions.
- **Inventory-aware order processing** that atomically deducts stock and prevents overselling.
- **Table availability and reservation conflict validation** to keep scheduling accurate.
- **Role-based access control** via a Managers group with protected APIs and UI.
- **JWT authentication** using `djangorestframework-simplejwt` (access + refresh tokens).
- **Production-ready settings** with environment segregation (`base.py`, `dev.py`, `prod.py`) and security hardening.
- **Responsive managers dashboard** with real-time team management.
- **Daily sales reporting and smart stock alerts** to highlight key metrics at a glance.
- **Admin access panel shortcut** for privileged users to reach Django admin quickly.
- **Comprehensive automated tests** for models, services, and REST endpoints.
- **Responsive frontend pages** (public landing + managers dashboard) with enhanced UX.

## Manager Dashboard & Reporting

Managers (or superusers) gain access to the `/managers/` dashboard, which now includes:

- **Team management table** to promote/demote staff into the Managers group.
- **Daily sales snapshot** summarising completed orders, revenue, and averages.
- **Low-stock alerts** when inventory dips near or below threshold levels.
- **Admin panel shortcut** linking directly to the Django admin interface.

All dashboard actions interact with authenticated API endpoints. Toast notifications surface successes or failures, and every endpoint performs defensive error handling.

## Tech Stack

- Python 3.8+
- Django 4.2+
- Django REST Framework
- Simple JWT
- PostgreSQL (production) / SQLite (development)
- WhiteNoise for static file serving
- JS + CSS for lightweight UI

## Project Structure

   ```
   restaurant_management_system/
    ├── manage.py
    ├── config/
    │ └── settings/
    | │ ├── init.py
    │ | ├── base.py
    │ | ├── dev.py
    │ | ├── prod.py
    │ ├── init.py
    | ├──urls.py
    | ├──asgi.py
    | ├──wsgi.py
    ├── restaurant/
    │ └── templatetags/
    │ | ├──init.py
    │ | ├── group_tags.py
    │ └── tests/
    │ | ├── test_models.py
    │ | ├── test_services.py
    │ | ├── test_views.py
    │ ├── init.py
    │ ├── admin.py
    │ ├── apps.py
    │ ├── exceptions.py
    │ ├── front_views.py
    │ ├── models.py
    │ ├── permissions.py
    │ ├── reports.py
    │ ├── serializers.py
    │ ├── services.py
    │ ├── urls.py
    │ └── views.py
    ├── templates/
    │ └── registration/
    | | ├──login
    │ ├── 404.html
    │ ├── base.html
    │ ├── index.html
    │ └── managers.html
    ├── static/
    │ ├── styles.css
    │ └── main.js
    ├── requirements.txt
    ├── Procfile
    ├── .env
    └── README.md
   ```

## Quickstart

1. **Clone & install dependencies**

   ```bash
    git clone <your-repo-url>
    cd restaurant_management_system
    python -m venv .venv
    source .venv/bin/activate  # use .venv\Scripts\activate on Windows
    pip install --upgrade pip
    pip install -r requirements.txt

   ```

2. **Configure environment variables**

   Create a .env file (for local development) using the template below:

   DJANGO_DEBUG=True
   DJANGO_SECRET_KEY=change-me
   DJANGO_ALLOWED_HOSTS=127.0.0.1,localhost

   For production deployments (config/prod.py), set the additional variables:

   DJANGO_DEBUG=False
   DJANGO_ALLOWED_HOSTS=your-domain.com
   DJANGO_CSRF_TRUSTED_ORIGINS=https://your-domain.com
   DJANGO_DB_ENGINE=django.db.backends.postgresql
   DJANGO_DB_NAME=restaurant_name
   DJANGO_DB_USER=restaurant_user
   DJANGO_DB_PASSWORD=super-secure-password
   DJANGO_DB_HOST=127.0.0.1
   DJANGO_DB_PORT=5432
   DJANGO_DB_REQUIRE_SSL=True
   JWT_ACCESS_MINUTES=20
   JWT_REFRESH_DAYS=14

   Optional overrides exist for email delivery (DJANGO_EMAIL_HOST, DJANGO_EMAIL_HOST_USER, etc.) and logging (DJANGO_LOG_LEVEL).

3. **Database & superuser**

   ```bash
   python manage.py migrate
   python manage.py createsuperuser

   ```

4. **Run the development server**

   ```bash
   python manage.py runserver

   ```

5. **Run automated tests**

   ```bash
   python manage.py test
   ```

## Reporting Endpoints

**Authenticated managers can query JSON reports**:

- GET /managers/reports/daily-sales/ – returns aggregated metrics for the current day (pass ?date=YYYY-MM-DD to look up a specific day).

- GET /managers/reports/stock-alerts/ – returns inventory items at or below threshold (use ?buffer=2 to include near-threshold items).

- The managers dashboard uses these endpoints automatically. You can also integrate them with BI tooling or scheduled jobs.

## Deployment Notes

- config/prod.py enforces DEBUG=False, secure cookies, HSTS, SSL redirects, and SMTP email.

- WhiteNoise serves static files with CompressedManifestStaticFilesStorage.

- Database settings default to PostgreSQL with optional SSL enforcement.

## Contributing

- Fork the repository.
- Create a feature branch.
- Commit with detailed messages and automated tests.
- Open a pull request describing your changes.
