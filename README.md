# Django CRM

A small server-rendered Django application for maintaining client records and assigning them to categories. The project uses Django MVT, Django authentication, model forms, the messages framework, and SQLite.

## Features

- Public account registration and sign-in with Django's built-in authentication forms.
- Staff-only dashboard, client search, client details, and client create/update/delete workflows.
- Staff management of categories and clients through Django admin.
- Client lists paginated at 25 records per page, with category data loaded efficiently.
- CSRF-protected POST requests for logout and deletion.
- Django success and information messages.

## Technology

- Python 3.12
- Django 5.2.18
- SQLite
- django-crispy-forms and crispy-bootstrap4
- Bootstrap 5 templates
- Ruff for linting and formatting
- GitHub Actions for checks and tests

Dependencies are pinned in `requirements.txt`; development tooling is in `requirements-dev.txt`.

## Project structure

```text
main_CRM/          Django project settings and root URLs
web_app/           Models, forms, views, app URLs, tests, migrations
templates/         Django templates and shared page components
.github/workflows/ GitHub Actions CI
manage.py          Django management entry point
```

## Install and run

Create a new virtual environment (keep any existing local environment separate), then install dependencies. On Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements-dev.txt
$env:DJANGO_DEBUG = "true"
$env:DJANGO_SECRET_KEY = (python -c "import secrets; print(secrets.token_urlsafe(50))")
$env:DJANGO_ALLOWED_HOSTS = "localhost,127.0.0.1,testserver"
python manage.py check
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Open `http://127.0.0.1:8000/`. Use `createsuperuser` for the initial administrator; do not put real secrets in source control. The project reads environment variables from the process. `.env.example` is a reference file and is not automatically loaded.

## Authentication and permissions

Anyone may register a regular account. Regular accounts can sign in and use the public home page, but do not receive access to client records or Django admin. Staff accounts may use the CRM and admin. There is no per-user client ownership: staff members share the same client records.

Use `python manage.py createsuperuser` for the initial administrator. An authorized administrator can create staff accounts in Django admin. Registration does not grant staff or superuser privileges.

## Categories and client workflows

Categories are managed in Django admin at `/admin/`; the project does not have a separate category-management page. Staff select a category when creating or editing a client. A category that still has clients cannot be deleted, protecting those records. SQLite is the configured database.

The staff dashboard supports adding clients, viewing and editing a record, deleting through a CSRF-protected POST form, searching by name or ID, and paging through results. Phone numbers are text values so new input can retain leading zeroes. The migration converts existing integer values to text, but cannot recover leading zeroes already lost before conversion.

## Configuration and deployment

Development defaults use `DJANGO_DEBUG=true` and local allowed hosts. For a production-like environment, set:

- `DJANGO_DEBUG=false`
- `DJANGO_SECRET_KEY` to a unique, high-entropy value of at least 50 characters
- `DJANGO_ALLOWED_HOSTS` to the exact comma-separated hostnames serving the app
- `DJANGO_SECURE_SSL_REDIRECT=true` (the default when debug is disabled)
- `DJANGO_SECURE_HSTS_SECONDS` only after confirming HTTPS is enforced for the site; include subdomains only if they are HTTPS-only too

Production startup fails if the secret is missing or weak, or if allowed hosts are missing. Secure session and CSRF cookies are enabled when debug is disabled. HSTS is opt-in so it is not enabled before a deployment's HTTPS policy is known. Run `python manage.py check --deploy` with the actual deployment environment before release.

The repository previously contained a development signing key and a SQLite database in Git history. Removing them from the current branch does not remove old commits, and `main` is not changed by this branch. If the key was ever used in a deployed environment, rotate it through the deployment operator. Privately review whether historical database copies contained personal data; do not publish those records. This project does not rewrite Git history automatically.

## Tests and quality checks

Tests use Django's isolated in-memory test database and do not use the local SQLite database:

```powershell
python manage.py test --verbosity 2
python manage.py check
python manage.py makemigrations --check --dry-run
python -m pip check
ruff check .
ruff format --check .
```

GitHub Actions runs these checks on pushes to `mahmoud` and pull requests targeting `main`.

## Known limitations

- Client records are shared across staff accounts; there is no per-record owner or multi-tenant separation.
- Category CRUD is available in Django admin, not in a separate application page.
- SQLite is the configured database; other database engines are not currently supported by project settings.
- Historical migration `0002` can fail if client rows already exist before the required category field is added and category ID `0` is absent. A regression test preserves this scenario but is skipped until an approved migration strategy is chosen; the existing local database was not migrated or changed.
- Historical Git commits may still contain the former database and development signing key.
- Browser-based visual testing has not been performed as part of this change.
