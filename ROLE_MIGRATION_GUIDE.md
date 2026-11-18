# Update your existing FoodLink project to Donor, Recipient and Admin

This guide is for your working project at:

`C:\Users\Lance Angel Escobana\Downloads\foodlink`

Use your existing Supabase project. Do not create a new database, delete tables, recreate accounts, delete migrations or overwrite `.env`. This update works whether or not you installed the previous Admin-promotion ZIP.

## What changes

| Account | After the update |
|---|---|
| Existing Admin | Remains Admin; same login and permissions |
| Existing Member | Must choose Donor or Recipient after signing in, before any dashboard/profile access |
| New registration | Must choose Donor or Recipient in the registration form |
| Donor | Own protected Donor dashboard |
| Recipient | Own protected Recipient dashboard |
| Admin | Own dashboard, role counts, user list and authority to promote active Donors/Recipients |

Existing Members are not assigned a role automatically. Their role is temporarily blank (NULL) in Supabase until they choose. This is an account setup state, not a fourth role. The choice is required, has no skip button and cannot select Admin. A chosen role cannot be changed through profile editing or by returning to the choice page. Existing logged-in Members are also directed to this page on their next request.

Passwords, names, emails, contact numbers, locations, account IDs and Admin accounts are retained. Donor/Recipient food listing and reservation features remain future phases; this update implements account functionality only.

## Step 1 — Stop the running server

In the VS Code terminal running Django, press **Ctrl+C** once. Wait until the command prompt appears.

Keep VS Code opened on your ORIGINAL project folder. Check that its terminal is here:

```text
(.venv) C:\Users\Lance Angel Escobana\Downloads\foodlink>
```

If you opened a new Command Prompt terminal, use:

```bat
cd /d "C:\Users\Lance Angel Escobana\Downloads\foodlink"
.venv\Scripts\activate.bat
```

## Step 2 — Back up the current project and Django data

Before replacing any files:

1. Open Windows File Explorer and go to Downloads.
2. Copy the current `foodlink` folder.
3. Paste a copy beside it and rename the copy `foodlink_backup_before_roles`. Use a different backup name if that name already exists.
4. Keep working in the original `foodlink` folder, not the backup.

In the original project's active terminal, export the existing Django data:

```bat
python manage.py dumpdata --all --indent 2 --output "..\foodlink_before_role_update.json"
```

Wait for the command prompt to return. Confirm `foodlink_before_role_update.json` exists in Downloads. If a file with that name already exists, use a new filename to avoid overwriting an older backup. If the export fails, stop and resolve that error before replacing files.

This export contains Django-managed records, including accounts and password hashes; it is not a complete Supabase service backup. Keep it private. The folder backup retains your old source code and database configuration.

## Step 3 — Download and extract the revised ZIP separately

1. Download the revised ZIP from this conversation.
2. Right-click it in File Explorer and select **Extract All**.
3. Extract into a SEPARATE folder, such as `FoodLink_Roles_Update` in Downloads.
4. Open its inner `foodlink` folder. You should see `manage.py`, `accounts`, `config`, `templates`, `static` and the guide files.

Do not rename or replace your entire existing project folder. Do not launch the project from inside the ZIP.

## Step 4 — Copy the updated source files

From the newly extracted inner `foodlink` folder, copy these FOUR folders:

- `accounts`
- `config`
- `templates`
- `static`

Paste them into your ORIGINAL folder:

`C:\Users\Lance Angel Escobana\Downloads\foodlink`

Choose **Replace the files in the destination** when Windows asks. This merges the folders and adds the new files, including the migration.

Also copy these three documents if you want the revised instructions in your project:

- `README.md`
- `UPDATE_INSTRUCTIONS.md`
- `VERIFICATION.md`

**Keep your original `.env` and `.venv`.** Do not replace `.env` with `.env.example`. No dependency changes are required from the previous ZIP. Do not copy an entire `foodlink` folder into your existing `foodlink` folder, which would create a nested project.

Confirm this new file now exists in your original project:

`accounts\migrations\0002_donor_recipient_roles.py`

The old `0001_initial.py` must still be present. Do not run `makemigrations` or delete migration files.

## Step 5 — Verify your existing Supabase connection

In your original project's terminal:

```bat
python manage.py check_database
```

Expected:

```text
PostgreSQL connected. foodlink schema is ready.
```

If this fails, check that the original `.env` is still there. Do not change the database password or create a new Supabase project just for this update.

## Step 6 — Apply the role migration

Run:

```bat
python manage.py migrate
```

Expected new migration:

```text
Applying accounts.0002_donor_recipient_roles... OK
```

This changes existing MEMBER records to an unset role so the users must choose for themselves. ADMIN records remain unchanged. It updates the role constraint to allow Donor, Recipient, Admin or the temporary unset state.

If it says **No migrations to apply**, verify the status below. If it fails, do not start the server or delete/recreate tables; save the error and ask for help.

## Step 7 — Confirm migration status and run checks

```bat
python manage.py showmigrations accounts
```

Both lines should have `[X]`:

```text
accounts
 [X] 0001_initial
 [X] 0002_donor_recipient_roles
```

Then run:

```bat
python manage.py check
python manage.py test accounts.test_without_database --verbosity 1
```

Expected: no system-check issues, then **22 tests** and **OK**. This test command does not create a test database or change Supabase data. Do not run the full database test suite against your live Supabase project.

## Step 8 — Restart the system

```bat
python manage.py runserver
```

Keep the terminal open and visit:

http://127.0.0.1:8000/

If the form styling appears unchanged, press **Ctrl+F5** in the browser.

## Step 9 — Test the mandatory choice for an existing Member

1. Log out of the Admin account if it is still signed in.
2. Log in using an account you previously registered as a Member. Use the same username/email and password as before.
3. Confirm you see **Choose your account preference**.
4. Try submitting without selecting a preference: the form must require a choice.
5. Before making a choice, type `http://127.0.0.1:8000/accounts/profile/` into the address bar. You must return to the choice page.
6. Select **Donor** or **Recipient** and click **Save and continue**.
7. Confirm the matching dashboard appears.
8. Log out and log back in. You should go directly to the chosen dashboard; you are not asked again.

You can log out without choosing, but you must choose before using the account next time. No existing Member account is converted to Donor or Recipient on behalf of the user.

## Step 10 — Test new registrations

1. Log out and open Register.
2. Fill in all fields, including Account preference.
3. Choose Donor and register a new account using an unused username/email.
4. Log in and confirm the Donor dashboard appears.
5. Repeat with another new account choosing Recipient.
6. Confirm Admin is not a registration option.

First name, last name, username, email, contact number and location remain mandatory. No profile photo is required.

## Step 11 — Test role isolation

While signed in as a Donor, visit:

- `http://127.0.0.1:8000/dashboard/recipient/`
- `http://127.0.0.1:8000/dashboard/admin/`

Both should show Access denied. A Recipient should also be denied the Donor and Admin dashboards. An Admin should be denied the Donor and Recipient dashboards.

## Step 12 — Test Admin promotion

1. Log in using your original Admin account. You do not need to recreate it.
2. Click **Manage user roles** on the Admin dashboard.
3. Find an active Donor or Recipient.
4. Click **Make Admin** and confirm the selected username.
5. Click **Confirm promotion**.
6. Log out and sign in as the promoted account. It should now open the Admin dashboard and be able to promote other Donors/Recipients.

Accounts still awaiting their choice cannot be promoted through this screen. Let those users choose first. Promotion grants FoodLink Admin authority; it does not grant Django staff/superuser access. The original superuser retains advanced `/admin/` access. Promotions are recorded in that user's Django admin history.

## Optional — Verify stored roles in Supabase

In Table Editor select schema `foodlink`, then table `accounts_user`.

- `ADMIN`: administrator.
- `DONOR`: donor.
- `RECIPIENT`: recipient.
- Blank/NULL: an existing Member has not chosen yet.

Do not manually fill pending roles if you want each user to make the mandatory choice themselves.

## If something goes wrong

- Missing `choose_role`/`promote_user` or missing template: copy all four folders again; do not mix old views and new templates.
- Constraint error mentioning `valid_role`: confirm migration 0002 is checked `[X]`.
- `No migrations to apply` but 0002 is not listed: verify that you copied into the folder containing the `manage.py` your terminal is using.
- An existing user goes straight to a Donor/Recipient dashboard: check the stored role; that user may already have chosen. Existing Admins intentionally skip the choice page.
- Do not restore only the old code after migrating: the old version does not understand the new roles. Keep the backup and seek help for a coordinated rollback. Reversing migration 0002 converts Donor/Recipient/unset roles back to MEMBER and therefore discards the role choices.

## Verification limit

22 database-independent tests passed during preparation. 23 PostgreSQL integration tests, including an actual migration-preservation test, are included but could not run because this workspace blocks local PostgreSQL sockets. The steps above provide the remaining verification on your Supabase-connected local installation. No SQLite fallback was used.
