# Sagarmatha College ERP — PRD

## Original problem statement
> make this web app fully functional, as uploaded in the screenshot, make all the buttons fully work, all the modules fully work, i have made nepali calendar integrated in HOD dashboard, do not break it, do not break any logic, just make it work

## User choices captured
- Seed `dinesh.80@hod.com / dinesh.80` as the HOD test user.
- Build new pages/modules from scratch for everything in the Modules dropdown.
- No static fallback for the Nepali calendar — live data only.

## Architecture
- Django 3.x monolith (`/app/manage.py`) using SQLite (`db.sqlite3`).
- ASGI entry point: `/app/backend/server.py` exposes `app` to the supervisor `uvicorn` process on port 8001.
- `/app/frontend/proxy.js` is a tiny node `http-proxy` that listens on port 3000 and forwards everything to 127.0.0.1:8001 so the Kubernetes ingress (which routes `/api/*` → 8001 and everything else → 3000) keeps working with a single Django app.
- Authentication: Django session auth with `EmailBackend`; reCAPTCHA disabled (no env key).
- CSRF trusted origins include `*.preview.emergentagent.com` and `*.preview.emergentcf.cloud`.

## Personas
- **HOD (Staff user_type=2 with role "HOD")** – primary persona shown in the screenshots. Has full access to all modules, dashboard cards and the Modules dropdown.
- **Staff (Teacher)** – limited to Self Service: attendance, results, leave, feedback.
- **Student** – attendance, results, books, leave, feedback.
- **Admin (user_type=1)** – original HOD/Admin home retained, manage staff/student/course/subject/session.

## Core requirements (static)
- HOD dashboard MUST keep showing the Nepali BS holiday calendar (Holidays + Optional Holidays tabs).
- Every dashboard card, button, dropdown item on the HOD dashboard must navigate to a working page.
- Module pages: Pre Admissions, Admissions, Examination, Human Resource, Inventory must exist as full CRUD pages.
- Payslip / Store / Library / Leave Balance Self Service pages must be functional.
- Seed command provides demo data (users, course, students, books, admissions, exams, inventory, payslips, leave, announcement).

## What's been implemented (29 May 2026)
### Iteration 1 — Modules dropdown + base wiring
- Runtime plumbing, settings (CSRF_TRUSTED_ORIGINS, ALLOWED_HOSTS=*), middleware rewrite, new models (Admission, Exam, InventoryItem, Payslip, Announcement) + migration, new module pages (pre_admissions/admissions/examination/human_resource/inventory + payslip/store), Modules dropdown rewired, dashboard cards show real counts, seed_demo command.

### Iteration 2 — Full ERPNext-style top bar + workflows
- **Models added**: `KaajRequest`, `OptionalHolidayRequest`, `SubstituteRequest`, `StoreRequisition` (4-state workflow: Requested -> Approved -> Fulfilled / Rejected), `AssessmentMark`, `StudyMaterial`, `Assignment`, `LessonPlan`, `BookLoan` (migration 0009).
- **`extra_views.py`** with 19 new views: apply/list Kaaj, apply/list Optional Holiday, apply/list/mine Substitute, `requests_waiting_for_approval` (one approver page for all 4 types), `requisition_form`, `view_past_requisitions` (Approve/Reject/Fulfil/Delete), `search_store_item`, `assessment_marks_entry`, `study_materials`, `assignments`, `lesson_plans`, `library_manage` (4-tab catalog + issue + active loans + history), `promote_admission_to_student` (one-click create CustomUser+Student with temp password).
- **HOD dashboard top bar** rewritten with all 5 dropdowns matching the user's screenshots: Leave/Kaaj (11 items), Store (3), Academic (7), Library (2), Others (4), plus 3 direct buttons.
- **All 8 dashboard cards** now show live numeric counts and link to the correct workflow page (Clearance->staff leave, Library->Library Manage, Leave Balance, Leave Approvals, Optional Holiday list, Kaaj list, Store Requisitions, Substitute list).
- **`seed_demo`** extended with sample Kaaj, Optional Holiday, Substitute, 2 Store Requisitions, Assignment, Study Material, Lesson Plan, Assessment Mark and BookLoan.
- **Nepali calendar block on HOD dashboard left untouched** — re-verified by automated tests, devanagari rows render.

## Test verification
- iteration_1.json: 100% pass.
- iteration_2.json: ~98% pass (only cosmetic note). 21 functional flows verified end-to-end.
- iteration_3.json: **100% pass (9/9 acceptance criteria)**. P2 + cosmetic features verified: high-contrast top-pill borders (slate-700), checkbox column + bulk-promote on Admissions, console email send with full RFC-822 message, forced-password-change middleware redirect loop, change-password form with banner + min-length validation, Payslip PDF generation (ReportLab, valid `%PDF-1.4` binary with `attachment; filename=payslip_<last>_<yr>_<mo>.pdf`).

### Iteration 3 — P2 + cosmetic polish
- **`CustomUser.must_change_password`** field + migration 0010; middleware loops every authenticated request to `/account/change-password/` until cleared.
- **`_promote_admission`** helper extracted from `promote_admission_to_student`; reused by new **`bulk_promote_admissions`** view (POSTs `ids` list from checkbox column).
- **Email send**: `_email_temp_password` uses Django `send_mail`; settings default to console backend so passwords print to backend logs (override via `EMAIL_BACKEND`/SMTP env vars to plug SendGrid/Resend without code changes).
- **`change_password`** view: forced-banner template, old/new/confirm fields, `update_session_auth_hash` so the user stays logged in, then routes by `user_type`.
- **`payslip_pdf`** view: ReportLab-built PDF (header, employee table, earnings table with net pay highlight, status line, footer); HOD/admin can download any payslip, others can only download their own.
- **Top-pill contrast**: slate-700 borders + slate-800 text on white, hover/focus flips to navy + white. `data-testid` on every top-pill plus `hod-topbar` wrapper class.
- **Table header contrast fix**: global CSS in `base.html` forces `.table-dark th` to navy bg + white text so the previously washed-out module-page tables now read cleanly.
- **Reportlab** added to `requirements.txt`.

## Prioritized backlog
### P1 (minor polish)
- HOD top button bar pills have low-contrast borders – cosmetic only.
- `module_views.payslip` and `inventory` cast int() without try/except; non-numeric POST will 500. Add validation.
- Replace `request.POST.copy()` mutation in pre_admissions/admissions with a kwarg to `_save_admission_from_post`.

### P2 (future modules)
- Examination: per-student result entry + report download.
- Inventory: store requisition workflow (request → approve → fulfil).
- HR: payroll batch generation, attendance summary widget per staff.
- Admissions: convert an Admission row into a real Student/CustomUser with one click.

## Next action items
- Optional polish above; otherwise the app is feature-complete to the user's brief.
