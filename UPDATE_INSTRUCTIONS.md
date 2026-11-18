# Apply the FoodLink hybrid UI update

This update adds Bootstrap 5 via CDN, black-to-blue gradients, glass accents, solid readable forms/tables and dark/light mode. Django still renders every page. No React, npm installation or frontend build is required.

## What is included

- Login, registration, mandatory role selection, Donor/Recipient/Admin dashboards, profile view/edit, role management and promotion confirmation.
- Responsive Bootstrap navbar, forms, alerts, pagination, tables and buttons.
- Required Donor/Recipient radio cards with no default choice.
- Dark/light toggle that follows the device setting initially, then remembers a choice in the browser. It is a browser preference, not a per-account database setting.
- Native Django administration keeps its own components, with a matching blue palette, Bootstrap CDN assets and shared theme toggle.
- Styled 403, 404 and 500 pages. Django normally shows its technical 404/500 details while DEBUG=True; the custom 404/500 pages are used with DEBUG=False.
- Inline SVG icons and local CSS; no external icon/font service or frontend framework.

## 1. Stop the server and make a backup

Press Ctrl+C in the terminal running Django.

In File Explorer, copy your current `foodlink` folder and name the copy `foodlink_backup_before_ui`. Keep working in the ORIGINAL folder. Keep this backup private; it contains your local `.env`.

Your existing database is not changed by this UI update. You do not need to recreate your accounts, repeat role choices or reset Supabase.

## 2. Extract the new ZIP separately

Right-click the new ZIP, choose Extract All, and extract it into a separate folder such as `FoodLink_UI_Update`. Open its inner `foodlink` folder.

Do not open the project from inside the ZIP, and do not replace your whole original project folder.

## 3. Copy these three folders

Copy these from the extracted project into your ORIGINAL project folder:

- `accounts`
- `templates`
- `static`

Choose Replace the files in the destination. The `accounts` folder includes the new `templatetags` helper used to render Bootstrap form controls, so copying only HTML/CSS is not enough.

Your original folder is:

`C:\Users\Lance Angel Escobana\Downloads\foodlink`

Keep your existing `.env`, `.venv`, `.git` and `.gitignore`. Do not copy `.env.example` over your real `.env`. Do not copy the entire `foodlink` folder into another `foodlink` folder.

Optionally copy `README.md`, `UPDATE_INSTRUCTIONS.md`, `VERIFICATION.md` and `ROLE_MIGRATION_GUIDE.md` to update your documentation. The `scripts` folder contains an optional JavaScript developer test; it is not needed to run the application.

No dependency updates are needed from the previous FoodLink ZIP. Do not run `makemigrations` for this UI update.

## 4. Check the existing role migration

In your original project terminal with `(.venv)` active, run:

```bat
python manage.py showmigrations accounts
```

You should already have:

```text
[X] 0001_initial
[X] 0002_donor_recipient_roles
```

You previously applied 0002 successfully. No additional database migration is part of this UI update. If 0002 is not applied, follow ROLE_MIGRATION_GUIDE.md first, including its configuration-folder update and data backup steps.

## 5. Run the checks

```bat
python manage.py check
python manage.py test accounts.test_without_database accounts.test_ui --verbosity 1
```

Expected: no system-check issues; 30 tests pass. This command does not write to Supabase or create a test database. Do not run the full `accounts` test suite against your live Supabase database.

If a new terminal is not activated, use Command Prompt:

```bat
cd /d "C:\Users\Lance Angel Escobana\Downloads\foodlink"
.venv\Scripts\activate.bat
```

## 6. Start the server and refresh

```bat
python manage.py runserver
```

Open http://127.0.0.1:8000/ and press Ctrl+F5 to refresh cached CSS and scripts.

Keep `DJANGO_DEBUG=True` for your existing local development setup. Bootstrap CSS and JavaScript load from jsDelivr, so keep internet access available. No `collectstatic` command is required when using Django's development server with DEBUG=True.

## 7. Try dark and light modes

1. Find the sun/moon button at the upper-right of the navbar. Its label names the mode it will switch to.
2. Click it to switch modes.
3. Navigate to another page; your choice should remain.
4. Refresh the page; the choice should still remain.
5. Open another tab for the same site; both tabs should use the saved theme.

Before you make a selection, the site follows your device's preferred color scheme. If browser storage is disabled, the toggle still works for the current page, but the browser cannot retain the preference. Use the same host (`127.0.0.1`) consistently; `localhost` has separate browser storage.

## 8. Check the pages and mobile layout

- Login: inputs readable in both modes; wrong credentials show an error.
- Registration: all required fields visible; Donor/Recipient cards are selectable; no Admin option.
- Pending-role screen: still requires a choice and offers no skip action.
- Dashboards: each role sees its own content; future modules remain clearly marked unavailable.
- Profile: edit your own details; validation errors are visible near fields.
- Admin: Manage user roles uses a table; Make Admin still opens a confirmation page before POSTing a change.
- Log out: still ends the session.
- Narrow the browser or use its mobile device view. Confirm the navigation menu opens and closes, forms fit the screen and the account table scrolls inside its own container.
- Check keyboard navigation and visible focus indicators. Reduced-motion device settings disable decorative transitions.

## 9. Commit the actual UI update

After checking your local pages:

```bat
 git status
 git add accounts templates static README.md UPDATE_INSTRUCTIONS.md VERIFICATION.md ROLE_MIGRATION_GUIDE.md
 git diff --cached --stat
 git commit -m "Style FoodLink with Bootstrap and dark-light themes"
 git push
```

If you did not copy the optional documents, omit those filenames from `git add`. Do not add `.env`, `.venv`, account-data exports or your backup folder.

## Troubleshooting

- `'ui' is not a registered tag library`: copy the entire updated `accounts` folder, including `templatetags/__init__.py` and `templatetags/ui.py`, then restart Django.
- Old styling: Ctrl+F5; check that `static/style.css`, `static/theme.js` and `static/ui.js` were replaced in the original project.
- Missing Bootstrap layout: check internet access or whether `cdn.jsdelivr.net` is blocked. The CDN assets are required for the intended layout. A basic JS navigation fallback is included, not a complete offline Bootstrap copy.
- Missing theme toggle: ensure JavaScript is enabled and `static/theme.js` loads successfully.
- Admin changes appear different from the public pages: advanced Django administration intentionally keeps native administration controls with a matching theme.
- Role migration errors: use ROLE_MIGRATION_GUIDE.md; do not delete tables or old migration files.

## Verification limits

30 database-independent Python tests and the JavaScript theme behavior checks passed here. Browser visual inspection could not run because this workspace blocks Chromium's local socket creation. Live PostgreSQL tests also remain unavailable here. Check the page layouts locally using the checklist above before submission.
