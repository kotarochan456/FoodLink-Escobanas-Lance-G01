# FoodLink PD2 — Windows update and GitHub submission guide

The core feature is Food Listing Management. This package retains the latest hybrid Django UI, account features and Donor/Recipient/Admin roles. It adds a PostgreSQL listing migration, full listing CRUD, role-based browsing, search and dashboard links. Bootstrap 5 is loaded via CDN; there is no React.

The code and local tests are complete. **GitHub PRs, verification on your Supabase project, browser screenshots and the final report are still pending.** No remote work has been claimed as done. Your deadline has not been provided: complete every push and merge before the exact deadline your instructor gives you.

## 1. Extract beside your current project

Extract `FoodLink_PD2_Update.zip` into:

`C:\Users\Lance Angel Escobana\Downloads\FoodLink_PD2_Update`

It contains `FoodLink_PD2.bundle`, `START_HERE.md`, and a `foodlink` folder with the revised source.

**Do not drag the new folder over your Git repository yet.** The recommended Git-bundle method below brings the revised files into your existing repository and preserves the two feature branches and commits. The source folder is an additional readable copy, not a replacement `.git` directory.

Use a VS Code **Command Prompt** terminal. Commands below are commands; file paths in explanations are not commands.

## 2. Back up your current work

Stop runserver with Ctrl+C. In Command Prompt:

```bat
cd "C:\Users\Lance Angel Escobana\Downloads\foodlink"
.venv\Scripts\activate.bat
git status
git remote -v
```

If `(.venv)` is already in your prompt, activation is unnecessary. Do not type `.envpython` or a migration file path.

If `git status` lists changes, copy the whole folder to a separate backup location first. Keep your `.env` private. Do not discard local changes. If they are project code that should be kept, commit them on an appropriately named feature branch, not main, before switching branches. If Git reports a conflict or the checks below fail, stop and share the exact error rather than running reset/force-push.

With a clean working tree:

```bat
git bundle create "..\foodlink_before_pd2.bundle" --all
python manage.py dumpdata --all --indent 2 --output "..\foodlink_before_pd2.json"
```

The JSON contains private account data and password hashes: keep it outside the repository and do not upload it. It is a Django data export, not a complete Supabase backup. Preserve the Supabase database and existing migrations; this update does not require deleting anything.

## 3. Import the two prepared feature branches

```bat
git fetch origin
git fetch "..\FoodLink_PD2_Update\FoodLink_PD2.bundle" "refs/heads/feature/food-listing-crud:refs/remotes/pd2/food-listing-crud" "refs/heads/feature/food-listing-discovery:refs/remotes/pd2/food-listing-discovery"
git merge-base --is-ancestor origin/main pd2/food-listing-crud
echo %ERRORLEVEL%
```

The last line must print `0`. The bundle was based on main commit `1347cde` (Delete .env.example). If it prints `1`, your remote main has newer work not in this bundle: do not overwrite it. The changes need to be integrated with those commits first.

Confirm your remote URL is the same repository:

`https://github.com/kotarochan456/FoodLink-Escobanas-Lance-G01.git`

## 4. Create develop from main, then publish feature 1

Check whether develop already exists:

```bat
git branch --list develop
git branch -r --list origin/develop
```

If both outputs are empty, run:

```bat
git branch develop origin/main
git push -u origin develop
```

If origin/develop already exists but no local develop exists, use `git branch --track develop origin/develop`. Do not reset an existing develop branch. If develop contains changes beyond the bundle baseline, integrate them before proceeding.

Create the local feature branch from the imported prepared branch:

```bat
git switch -c feature/food-listing-crud pd2/food-listing-crud
git push -u origin feature/food-listing-crud
```

If that local branch already exists, use `git switch feature/food-listing-crud` and inspect its log instead of creating another branch.

On GitHub, open **Pull requests > New pull request**:

- Base: `develop`
- Compare: `feature/food-listing-crud`
- Title: `Add food listing CRUD with ownership and validation`
- Description: Donor listing create/read/update/delete, PostgreSQL migration, ownership checks, Recipient read-only access, Admin moderation, and retained hybrid account UI. Validation evidence is recorded in VERIFICATION.md.

Review the diff, create the PR and **Create a merge commit**. Do not choose squash/rebase for this prepared-history workflow. **Do not delete the feature branch.** Save the PR URL.

## 5. Apply feature 2 and test locally

After feature 1 is merged remotely:

```bat
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch -c feature/food-listing-discovery pd2/food-listing-discovery
git merge origin/develop
python -m pip install -r requirements.txt
python manage.py check_database
python manage.py migrate
python manage.py showmigrations listings
python manage.py check
python manage.py runserver
```

The merge incorporates the real GitHub merge commit into feature 2. Its source base was created from develop after integrating feature 1 locally. Feature 2 adds dashboard integration, Recipient discovery, filters, testing and report preparation.

`showmigrations listings` must show `[X] 0001_initial`. Existing users and roles remain. Keep your `.env` and Supabase credentials unchanged. Do not run `makemigrations`, delete account migrations, or recreate Supabase.

Open `http://127.0.0.1:8000/`. Follow every step in **VERIFICATION.md**. The new listing table is in Supabase's `foodlink` schema, named `listings_foodlisting`. Refresh after saving/editing and confirm values persist. Test account login, logout, profile edit and role boundaries too.

Do not run the full Django test suite against your existing Supabase database. The suite was run on disposable PostgreSQL; README explains how to repeat it safely on a separate test server.

## 6. Create evaluation accounts and capture screenshots

You may use your existing Donor/Recipient/Admin test accounts. Do not publish your personal admin password.

Alternatively, for this development/demo project, stop the server and run:

```bat
python manage.py create_demo_accounts
```

Enter a **test-only password** twice. This creates `pd2_donor`, `pd2_recipient`, and `pd2_admin`; it never overwrites an existing account and never grants staff/superuser access. It requires `DJANGO_DEBUG=True`. Start runserver again and log in as each account to confirm it works on your database. Replace the report's isolated-verification password with the password you actually chose. Use demo-only data because a public report makes these credentials public.

Capture these real browser screenshots with Win+Shift+S; save under `docs/screenshots/`:

1. Donor dashboard with Share food / My listings.
2. Share-food form with a visible quantity or date validation error.
3. Saved listing detail and creation success message.
4. Edited listing with saved updated values.
5. Recipient filtered search results and detail view.
6. Admin listing management / a completed listing.
7. Delete confirmation, followed by success and the removed listing.

Also check dark/light mode and mobile-width navigation. Do not include database passwords, `.env`, or personal data in screenshots.

## 7. Open the remaining PRs before finalizing the report

```bat
git push -u origin feature/food-listing-discovery
```

Create a second PR with base `develop`, compare `feature/food-listing-discovery`, title `Add food discovery dashboards and PD2 documentation`. Leave it open while finishing the report. Save its URL.

Create the release PR with base `main`, compare `develop`, title `Release PD2 Food Listing Management`. It can be opened now because feature 1 is already in develop. Leave it open; feature 2 will be included automatically after its merge. Save this third URL.

## 8. Finish the required report

Open `docs/FoodLink-Escobanas-Lance-G01-PD2.docx` in Word (or LibreOffice Writer). It is filled from the instructor's exact template and retains all sections, but it is clearly marked as a preparation draft.

- Enter the actual submission date; verify your name and section.
- Replace all three pending PR-link entries with the real URLs from steps 4 and 7.
- Add your labeled browser screenshots in the Screenshots section, including the validation error.
- Update Test Accounts to the three accounts/passwords you verified locally against your Supabase database.
- Update remaining tasks and outstanding issues to the truth after your checks.
- Remove the draft notice only once its pending items are finished. Review the declaration before submission.
- Export as PDF, replacing `docs/FoodLink-Escobanas-Lance-G01-PD2.pdf`. Do not rename it or remove any section.

Commit the finished documents and screenshots on feature 2:

```bat
git status
git check-ignore .env
git ls-files .env
git add docs
git commit -m "Complete PD2 report with workflow links and UI evidence"
git push
```

`git check-ignore .env` should print `.env`; `git ls-files .env` should print nothing. Also ensure no `.venv/`, `venv/`, `__pycache__/` or backup JSON is staged. Adding a path to `.gitignore` does not remove secrets from earlier history; if credentials were previously published, replace those credentials separately.

## 9. Merge feature 2, then release

Review and merge the second PR into develop using **Create a merge commit**. Keep the feature branch.

Review the release PR into main. Confirm its Files changed includes the finalized PDF, listings app, templates, updated README and migration. Merge only after local verification passes. Keep develop and both feature branches.

Then synchronize your computer without making a direct commit on main:

```bat
git fetch origin
git switch develop
git pull --ff-only origin develop
git switch main
git pull --ff-only origin main
python manage.py migrate
python manage.py runserver
```

## 10. Check the submission

Open an incognito/private browser window and visit:

`https://github.com/kotarochan456/FoodLink-Escobanas-Lance-G01`

Confirm the repository is public, the PDF opens in `docs/`, both feature branches remain, both feature PRs are merged into develop, and the release PR is merged into main. Check commit/merge timestamps against the instructor's deadline. Local commits in the ZIP alone do not count as pushed work, and this package cannot recreate progress on earlier dates.

Submit the repository link through `https://forms.gle/5EjRcvs4yFKRRt1e6` after these checks. The form has not been submitted for you.
