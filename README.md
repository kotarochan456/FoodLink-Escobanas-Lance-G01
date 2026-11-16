# FoodLink — Account Feature (Donor, Recipient and Admin)

Full-stack Django: Python, Django templates, local HTML/CSS, and Supabase PostgreSQL. No React and no SQLite. Django handles authentication and sessions; Supabase is the database provider.

## Already running the previous version?

Follow **UPDATE_INSTRUCTIONS.md** from start to finish. Keep your original `.env` and `.venv`. Copy the four updated source folders, then run `python manage.py migrate` before starting the updated server. This update includes migration 0002.

## Implemented behavior

- Registration requires first name, last name, username, email, contact number, location, Donor/Recipient preference and matching passwords.
- Unique usernames and emails are enforced case-insensitively in validation and PostgreSQL constraints.
- Password hashing, password strength checks, username-or-email login, session logout, CSRF and clear messages.
- Separate Donor, Recipient and Admin dashboards, with role checks on the server.
- Existing MEMBER accounts are migrated to an unset role and must choose Donor or Recipient once. Middleware prevents bypassing the choice via dashboards, profile URLs or existing sessions. Logout remains available.
- Existing Admins keep their roles. No automatic Donor/Recipient assignment takes place.
- Public registration/role-choice forms never allow ADMIN. Profile editing never changes roles or another user's information.
- Admins can promote active Donors/Recipients after confirmation. Promoted Admins can promote others. Each actual promotion records its actor in Django admin history.
- Pending and inactive accounts cannot be promoted through the role-management screen.
- Ordinary promotion does not grant Django staff/superuser permissions. The bootstrap superuser retains advanced Django administration access.

Food listing CRUD, food browsing/reservation, search, history and notifications remain later phases. Dashboards explain each role's planned responsibilities without claiming those modules are implemented.

## 1. Install Python on Windows

Install Python **3.14** (64-bit) from https://www.python.org/downloads/windows/ . This project uses Django 5.2 LTS, compatible with Python 3.12–3.14. Avoid preview Python releases. Enable the installer's PATH option if offered, then close and reopen VS Code and Command Prompt.

Run `py --version`. If `python` opens the Microsoft Store, use `py` or disable the Python Store shortcuts in Windows App execution aliases. Tested here on Python 3.12.

## 2. Open the project and install dependencies

Extract the ZIP first. In VS Code open the `foodlink` folder containing `manage.py`. Use a **Command Prompt** terminal (Terminal > New Terminal > select Command Prompt).

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install -r requirements.txt
copy .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated secret into `DJANGO_SECRET_KEY` in `.env`, enclosed in double quotes. For PowerShell, activate using `.venv\Scripts\Activate.ps1`; if execution policy blocks it, use Command Prompt instead. Select `.venv` as the Python interpreter in VS Code.

## 3. Set up Supabase

1. Create a dedicated FoodLink project at https://supabase.com/ and retain its **database password**.
2. Open the project's SQL Editor. Paste and run the complete `supabase_setup.sql` file once. It creates a private `foodlink` schema. Do not add that schema to Data API exposed schemas.
3. Open **Connect**, choose **Session pooler**, and copy its host, port, database and username into `.env`. Use the session pooler, normally port 5432, not transaction mode on 6543. Use the actual values shown in your project, not the example placeholders.
4. Set `DB_PASSWORD` to the database password (not an anon key, service key or your Supabase account password). Keep it quoted; values are supplied separately so URL encoding is unnecessary. For a password containing a double quote, use single quotes around the value instead.
5. Keep `DB_SSLMODE=require`. Keep `DJANGO_DEBUG=True` only for local development.

Example structure (replace every placeholder):

```dotenv
DJANGO_SECRET_KEY="your-generated-secret"
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DB_NAME=postgres
DB_USER=postgres.YOUR_PROJECT_REF
DB_PASSWORD="your-database-password"
DB_HOST=your-session-pooler-host
DB_PORT=5432
DB_SSLMODE=require
```

The pooler username often includes the project reference. Copy it exactly. Your application uses a private schema so Django account/session tables are not in the default public API schema. Do not expose database credentials in templates or commit `.env`.

## 4. Create tables and the administrator

From the folder containing `manage.py`, with the virtual environment active:

```bat
python manage.py check_database
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

`check_database` must succeed before migration. Migrations are already included; you do not need `makemigrations` for initial setup.

`createsuperuser` asks for username, email, first name, last name, contact number, location and password. Password typing is hidden. It automatically creates the ADMIN role with Django administration access. Public sign-up allows only Donor or Recipient. After choosing their role, users can be promoted to Admin by an existing Admin.

Open http://127.0.0.1:8000/ . Register as a Donor or Recipient, then log in. Log out before testing the Admin account. Stop the server with Ctrl+C.

## Routes

| Page | URL | Access |
|---|---|---|
| Role dispatcher | `/` | Signed-in users |
| Register | `/accounts/register/` | Public; choose Donor or Recipient |
| Login | `/accounts/login/` | Username or email |
| Logout | `/accounts/logout/` | POST with CSRF |
| Mandatory choice | `/accounts/choose-role/` | Signed-in accounts awaiting their first choice |
| Donor dashboard | `/dashboard/donor/` | Donor only |
| Recipient dashboard | `/dashboard/recipient/` | Recipient only |
| Admin dashboard | `/dashboard/admin/` | Admin only |
| Manage roles | `/dashboard/admin/users/` | Admin only |
| Promote user | `/dashboard/admin/users/<id>/promote/` | Admin; GET confirms, POST changes |
| Own profile | `/accounts/profile/` | Selected role required |
| Edit own profile | `/accounts/profile/edit/` | Selected role required |
| Advanced administration | `/admin/` | Staff with permissions |

The old `/dashboard/member/` URL redirects through the role dispatcher for bookmark compatibility; there is no Member dashboard in the new system.

## Tests

Safe checks without database mutations (requires a configured secret):

```bat
python manage.py check
python manage.py test accounts.test_without_database --verbosity 1
```

The 22 database-independent tests check forms, roles, middleware, hashing, templates, CSRF and mocked database behavior. See VERIFICATION.md for the limits of these checks.

Run the 23 database-backed tests ONLY against a separate disposable PostgreSQL server with a role permitted to create test databases. Never point the full suite at live Supabase. Django creates and drops a test database; pooler permissions may prevent that. One test explicitly applies and reverses the role migration within the disposable test database.

Example Command Prompt configuration for your own disposable local PostgreSQL installation (create the empty `foodlink_test_source` database first):

```bat
set DB_HOST=127.0.0.1
set DB_PORT=5432
set DB_NAME=foodlink_test_source
set DB_USER=your_local_test_role
set DB_PASSWORD=your_local_test_password
set DB_SSLMODE=disable
python manage.py test accounts --verbosity 2
```

Open a new terminal afterwards to return to `.env` Supabase settings. Environment variables override `.env`. Test databases use the public schema in isolated PostgreSQL; deployed Supabase tables use the private foodlink schema.

## Code guide

- `accounts/models.py`: user fields and role/uniqueness constraints. NULL role means mandatory setup is pending, not an extra account type.
- `accounts/forms.py`: validated registration, role choice, login and profile forms.
- `accounts/backends.py`: username-or-email authentication.
- `accounts/middleware.py`: enforces role choice for legacy accounts, including active sessions.
- `accounts/views.py`: registration, dashboards, mandatory choice, private profiles and audited promotion.
- `accounts/admin.py`: advanced Django user administration.
- `accounts/migrations/0001_initial.py`: original schema, retained for existing installations.
- `accounts/migrations/0002_donor_recipient_roles.py`: preserves accounts, resets only legacy MEMBER role to NULL, updates role choices/constraint.
- `config/settings.py`: environment settings, PostgreSQL and middleware.
- `config/urls.py`: named routes.
- `templates/` and `static/`: Django frontend and local CSS.

## Troubleshooting

- Python not found: restart VS Code after installation and try `py --version`.
- Missing secret: create `.env` and set the generated secret.
- Tenant/user not found: copy username and host from the same Supabase Session pooler panel.
- Password authentication failed: use the database password, not an API key.
- Schema check fails: run `supabase_setup.sql` once for a NEW project only; preserve the existing schema when updating.
- Role constraint error: confirm migration 0002 is applied with `python manage.py showmigrations accounts`.
- Logout returns 405 in the address bar: use the Log out button; POST is required.

## Deployment scope

This is a local course-development project. Configure your own database before use. No credentials or default passwords are included. Internet deployment requires HTTPS, a production server, `DEBUG=False`, explicit hosts, protected secrets and login rate limiting. Do not expose the `foodlink` schema through Supabase's Data API.

Official references used for the original setup:
- https://docs.djangoproject.com/en/5.2/releases/5.2/
- https://docs.djangoproject.com/en/5.2/topics/auth/customizing/
- https://docs.djangoproject.com/en/5.2/topics/auth/default/
- https://supabase.com/docs/guides/database/connecting-to-postgres
