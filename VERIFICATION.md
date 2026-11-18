# Verification — Bootstrap hybrid UI update

Passed in this workspace:

- 30 database-independent Python tests: 22 existing account/role checks plus 8 UI rendering checks.
- JavaScript theme checks using Node's standard library: initial device setting, saved preference priority, toggle behavior, refresh persistence, unavailable storage, invalid saved values, device preference changes, cross-tab updates and accessible button labels.
- Django system checks: no issues.
- Model/migration comparison: no changes detected. The database migration-history connection was unavailable.

UI checks verify Bootstrap CDN includes, CSRF fields, required unselected public-role radios, preserved radio choice, form error associations, role-specific promotion links, dashboards/profiles/error templates and themed Django admin login. They are server-rendering checks, not browser screenshots.

Bootstrap 5.3.9 CDN URLs and SRI values were taken from the official introduction documentation. The delivery includes no React dependencies, no frontend build and no account credential files.

Not verified here:

- Browser visual inspection: Chromium could not start because the workspace blocks its local socket creation.
- 23 PostgreSQL integration tests: still included, not run here due to the same local socket restriction. Do not run these against the live Supabase project.

The user has confirmed migration 0002 succeeded on their local Supabase-connected installation. This UI update adds no model changes or migrations. Existing registration, role selection, session authentication, private profiles and promotion authorization are retained. Use UPDATE_INSTRUCTIONS.md for local visual and workflow checks before submission.
