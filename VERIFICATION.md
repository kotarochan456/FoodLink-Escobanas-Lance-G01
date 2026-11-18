# PD2 verification

Verified on 2026-11-18 with Python 3.12, Django 5.2.19 and disposable PostgreSQL 16.2.

- 69 Django tests pass: existing accounts, actual legacy-role migration, registration, username/email login, logout, profile ownership, role isolation, promotion, UI rendering and food-listing functionality.
- Listing tests exercise create/read/update/delete via HTTP views with persisted PostgreSQL data, owner-ID spoofing, cross-owner URL access, Recipient read-only restrictions, Admin moderation without staff access, required fields, quantity/date/status validation, expiry/scheduled/completed filtering, inactive owners, CSRF, escaping, search and pagination.
- `manage.py check` passes; `makemigrations --check --dry-run` reports no changes.
- Migrations and a saved listing were verified in a separate PostgreSQL database's private `foodlink` schema. All three optional demo accounts logged in successfully there.
- Existing Node theme checks pass. Node is optional and is not a runtime dependency.

## Limits

The supplied Supabase project was not accessed or changed. Browser screenshot capture was blocked by the execution environment's browser socket restriction; visual browser/mobile checks and report screenshots must be completed locally. No remote branches were pushed or PRs merged because GitHub write access was not connected. These are submission tasks, not completed claims.

Run the full suite ONLY against a disposable PostgreSQL server with permission to create and drop test databases. Use README instructions; do not point the test suite at your live Supabase pooler. The normal application remains configured for Supabase using your private `.env`.

## Manual acceptance flow

1. Register one Donor and one Recipient. Confirm required fields, duplicate username/email and mismatched password errors.
2. Log in by username and email. Confirm role routing and POST logout.
3. Update your profile and confirm another user's profile cannot be selected.
4. Donor: Share food; try quantity 0 and expiry before availability. Confirm validation errors and no record creation.
5. Save valid food. Confirm success, detail, and My listings. Edit it and refresh to confirm persistence.
6. Recipient: search for that food and view details. Direct create/edit/delete attempts must fail.
7. A second Donor must not see/edit/delete the first Donor's listing by URL.
8. Admin: manage all listings. Mark one Completed; Recipient must no longer see or open it.
9. Donor: create another listing; cancel deletion once, then confirm deletion. Verify it is gone after refresh.
10. Test scheduled and expired listings, light/dark modes, mobile navigation, and legacy mandatory role choice.

Capture labeled screenshots during steps 1, 4, 5, 6, 8 and 9 for the report. Use demo food and test accounts only.
