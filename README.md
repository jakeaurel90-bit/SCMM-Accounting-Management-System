# Ledger — Church Finance Dashboard (Django)

A full-stack Django site built from two static HTML mockups, now backed by a
real database with working forms, navigation, and PDF generation:

- **Pastor Dashboard** (`/pastor/`) — salary status, salary history, branch
  giving report, and an editable profile.
- **Finance Office Dashboard** (`/finance/`) — build an evangelism budget
  allotment, manage pastors, record salary payments, and send allotment
  notices to pastors.

There's no login system yet, so the pastor pages always show the
first `Pastor` record in the database (seeded as Rev. Ramon Dizon). See
"Next steps" below for adding real authentication.

## Login & demo accounts

Every page now requires logging in — there's a real login/logout flow using
Django's auth system. On first `migrate`, a data migration creates one
demo account for you:

| Role | Username | Password | Lands on |
|---|---|---|---|
| Finance office | `treasurer` | `treasurer123` | `/finance/overview/` |

**Pastors are no longer seeded** — the Pastors list starts empty on
purpose. Log in as `treasurer` and go to **Pastors** (`/finance/pastors/`)
to add, edit, or delete pastor records from there. Deleting a pastor also
removes their salary history and branch reports (you'll get a confirmation
prompt first).

**Giving a pastor their own login** is done from that same page — click
**Edit** on any pastor, then:
- **Create Login** — set a username + password (min. 6 characters) so they
  can sign in and see their own `/pastor/...` dashboard.
- **Reset Password** — change their password at any time.
- **Revoke Login** — deletes their login entirely (their pastor record and
  history stay intact; they just can't sign in anymore).

The Pastors list also shows a **Login** column so you can see at a glance
who has access and who doesn't.

Access rules:
- Pages under `/pastor/*` require a logged-in user linked to a `Pastor`
  record. Each pastor only ever sees their own dashboard (there's no way
  to view someone else's data by guessing a URL).
- Pages under `/finance/*` require a logged-in **staff** user (`is_staff=True`).
- Anyone signed out is redirected to `/login/`.
- The **Log Out** button lives at the bottom of both sidebars.

⚠️ Change the demo treasurer password (or delete/replace the account)
before putting this anywhere other people can reach.

## What's functional

| Area | What it does |
|---|---|
| Nav bar (both sidebars) | Every link routes to a real page — no more `#` placeholders. |
| Download PDF Slip / Download PDF | Generates and downloads a real PDF salary slip (via `reportlab`). |
| New Line Item (finance) | Submits a form that creates a `BudgetItem` row, shown immediately in the table and totals. |
| Edit (budget table) | Opens an edit page to update or delete that line item. |
| Send Allotment | Selecting channels + recipients and clicking Send creates a log entry (`SentAllotment`), visible on the Sent History page. Checkbox counts update live via a small bit of JS. |
| Pastors page | Lists all pastors (starts empty) — add, edit, or delete any pastor. |
| Pastor login management | Create/reset/revoke a pastor's login right from their Edit page — no need to touch Django admin. |
| Salary Payments page | Lists all payments and lets you record a new one (which then shows up in that pastor's salary history). |
| Sent History page | Full log of every allotment sent, with channels/recipients/totals. |
| Settings page | Edit the organization name and treasurer title shown in the finance sidebar. |
| Profile page | Pastor can update their own contact details. |

All of this is backed by SQLite via Django's ORM — nothing is hardcoded in
the templates anymore.

## Project structure

```
church_ledger/
├── manage.py
├── requirements.txt
├── .env.example
├── config/                        # Django project (settings, root urls)
├── dashboard/                      # The app
│   ├── models.py                  # Pastor, SalaryPayment, BranchReportEntry,
│   │                               # BudgetItem, SentAllotment, OrgSettings
│   ├── forms.py                    # ModelForms for every page's form
│   ├── views.py                    # Page logic + all POST actions
│   ├── urls.py
│   ├── admin.py                    # All models registered for /admin/
│   ├── migrations/
│   │   └── 0002_seed_demo_data.py # Auto-seeds demo data on first migrate
│   └── templates/dashboard/
│       ├── base.html
│       ├── _pastor_nav.html        # Shared pastor sidebar (all pastor pages)
│       ├── _finance_nav.html       # Shared finance sidebar (all finance pages)
│       ├── _messages.html          # Shared success/error banner
│       ├── index.html
│       ├── pastor_dashboard.html / salary_history.html / branch_reports.html / profile.html
│       └── finance_dashboard.html / edit_budget_item.html / finance_overview.html /
│           pastors_list.html / salary_payments.html / sent_history.html / settings.html
└── static/css/
    ├── base.css                    # shared layout/design tokens + form/message styles
    ├── pastor_dashboard.css
    └── finance_dashboard.css
```

## Setup (local development)

1. **Clone the repo and enter it**
   ```bash
   git clone <your-repo-url>
   cd church_ledger
   ```

2. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables (optional for local dev)**
   Copy `.env.example` to `.env` and adjust values if needed. The project
   falls back to safe development defaults if you skip this step.

5. **Apply migrations** — this creates `db.sqlite3` *and* seeds it with the
   original demo data (Rev. Dizon, the 5 pastors, the 3 budget line items,
   etc.) via a data migration, so the site looks right the first time you
   open it.
   ```bash
   python manage.py migrate
   ```

6. **Run the development server**
   ```bash
   python manage.py runserver
   ```

7. Visit:
   - `http://127.0.0.1:8000/` — landing page (links depend on whether you're logged in)
   - `http://127.0.0.1:8000/login/` — log in as a pastor or the treasurer (see credentials below)
   - `http://127.0.0.1:8000/pastor/` — pastor dashboard (requires pastor login)
   - `http://127.0.0.1:8000/finance/` — finance office dashboard (requires treasurer/staff login)
   - `http://127.0.0.1:8000/admin/` — Django admin (create a superuser first
     with `python manage.py createsuperuser`) — handy for quickly editing
     any record without going through the forms.

## Using this in VS Code

- Open the project folder in VS Code.
- Select the `venv` interpreter (Command Palette → "Python: Select Interpreter").
- Use the built-in terminal for the `manage.py` commands above.
- The **Python** extension will give you linting/autocomplete for the Django code.

## Next steps to make this even more "real"

- **Self-service password reset**: pastors currently can't reset their own
  forgotten password — only the treasurer can (via the Reset Password
  button on their Edit page). Add Django's built-in
  `PasswordResetView`/email flow if pastors need to do this themselves.
- **Real email/SMS sending**: "Send Allotment" currently just logs the
  action (`SentAllotment`) — wire it up to an actual email backend / SMS
  provider if you want pastors to really receive it.
- **Finer-grained permissions**: right now any staff user has full finance
  access and any linked pastor sees only their own data — add Django
  Groups/permissions if you need more roles (e.g. read-only auditor).

## Deploying

Before deploying anywhere public:

- Set a strong, secret `DJANGO_SECRET_KEY` environment variable.
- Set `DJANGO_DEBUG=False`.
- Set `DJANGO_ALLOWED_HOSTS` to your real domain(s).
- Run `python manage.py collectstatic` to gather static files into
  `staticfiles/` for your web server to serve.
- Switch `DATABASES` in `config/settings.py` to a production database (e.g.
  PostgreSQL) if SQLite isn't sufficient for your traffic.

## Uploading to GitHub

```bash
git init
git add .
git commit -m "Full-stack Django conversion with working forms and PDF export"
git branch -M main
git remote add origin <your-repo-url>
git push -u origin main
```

`.gitignore` already excludes the virtual environment, `db.sqlite3`, `.env`,
and other files that shouldn't be committed. Since `db.sqlite3` is
gitignored, anyone who clones the repo gets a fresh, auto-seeded database
the first time they run `python manage.py migrate`.
#   S C M M - A c c o u n t i n g - M a n a g e m e n t - S y s t e m  
 