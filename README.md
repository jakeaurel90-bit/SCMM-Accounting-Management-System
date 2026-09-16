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
| Send Allotment | Selecting channels + recipients and clicking Send creates a log entry (`SentAllotment`), visible on the Sent History page. If "Email" is checked, a real email is sent via SMTP to every selected pastor with an address on file. If "SMS" is checked and Twilio is configured, a real text is sent to every selected pastor with a phone number on file (auto-converted to `+63...` format). Messenger is logged only. Checkbox counts update live via a small bit of JS. |
| Messenger contact link | The MSGR tag on each recipient card is a real clickable link that opens `https://m.me/...` in a new tab. |
| Pastors page | Lists all pastors (starts empty) — add, edit, or delete any pastor. |
| Pastor login management | Create/reset/revoke a pastor's login right from their Edit page — no need to touch Django admin. |
| Salary Payments page | Lists all payments and lets you record a new one (which then shows up in that pastor's salary history). |
| Sent History page | Full log of every allotment sent, with channels/recipients/totals. |
| Settings page | Edit the organization name and treasurer title shown in the finance sidebar. |
| Profile page | Pastor can update their own contact details. |

All of this is backed by SQLite via Django's ORM — nothing is hardcoded in
the templates anymore.

## Sending real emails

"Send Allotment" sends a real email to every selected pastor who has an
address on file, whenever the **Email** channel is checked. Without any
provider configured, emails are simply printed to your terminal instead —
nothing breaks, nothing gets lost, it's just not delivered anywhere. This
is the default for local development.

There are two ways to send for real, and **which one you need depends on
where the app is running**:

### On Render (or any host that blocks outbound SMTP): use Brevo

Render — like most cloud hosts — blocks outbound traffic on the SMTP
ports Gmail uses, to prevent spam abuse. Gmail's SMTP will **never work**
from Render, no matter how it's configured (it'll hang until the request
times out with an Internal Server Error). Use
[Brevo](https://www.brevo.com)'s HTTP API instead, which works because
it's just a normal HTTPS request — and unlike SendGrid, Brevo isn't part
of Twilio, so it isn't affected by Twilio's regional trial restrictions
(this matters if you're sending from a Philippines-based account).

1. Sign up at <https://www.brevo.com> (free tier: 300 emails/day,
   forever, no card required).
2. Settings → Senders, Domains & Dedicated IPs → **Senders** → Add a
   Sender — enter the email address you want to send from and confirm it
   via the email Brevo sends you.
3. Settings → SMTP & API → **API Keys** tab → Generate a new API key.
   Copy it immediately.
4. On Render: web service → Environment tab → add:

   | Key | Value |
   |---|---|
   | `BREVO_API_KEY` | the key you just copied |
   | `DEFAULT_FROM_EMAIL` | the exact address you verified as a Sender |

5. Save — Render redeploys automatically. From then on, "Send Allotment"
   with Email checked really sends, via `dashboard/emailing.py`.

### Locally, or on a host that doesn't block SMTP: Gmail App Password works fine

If you're not on Render (or your host doesn't block SMTP), plain Gmail
SMTP is simpler to set up than SendGrid:

1. On the Google account you want to send from, turn on
   **2-Step Verification** (Google Account → Security).
2. Go to <https://myaccount.google.com/apppasswords> and create an
   **App Password** — a 16-character code, *not* your normal Gmail password.
3. Set these values (locally: in `.env`, which loads automatically):

   | Key | Value |
   |---|---|
   | `EMAIL_HOST_USER` | your full Gmail address |
   | `EMAIL_HOST_PASSWORD` | the 16-character App Password (no spaces) |
   | `DEFAULT_FROM_EMAIL` | optional — defaults to `EMAIL_HOST_USER` if unset |

**If both `BREVO_API_KEY` and Gmail credentials are set, Brevo wins**
— `dashboard/emailing.py` checks for it first. Other SMTP providers
(Mailgun, Outlook, your own mail server) work the same way as Gmail via
`EMAIL_HOST`/`EMAIL_PORT`/`EMAIL_USE_TLS`, for hosts that don't block SMTP.

## Sending real SMS

"Send Allotment" can also send a real text message to every selected
pastor with a phone number on file, via [Twilio](https://www.twilio.com).
Unlike email, there's no free option here — Twilio is a paid,
pay-per-message service (carriers charge for SMS delivery), and you'll
need to buy a phone number to send from.

Without Twilio configured, SMS stays exactly as before: logged in the
Sent History, but not actually delivered.

### Setting it up

1. Create a Twilio account and buy a phone number that can send SMS
   (Twilio's console walks you through this — trial accounts get a small
   free credit to test with).
2. From the Twilio Console, copy your **Account SID** and **Auth Token**.
3. Set these values (locally: in `.env`; on Render: as environment
   variables):

   | Key | Value |
   |---|---|
   | `TWILIO_ACCOUNT_SID` | starts with `AC...` |
   | `TWILIO_AUTH_TOKEN` | from the Twilio Console |
   | `TWILIO_FROM_NUMBER` | your Twilio number, in `+1XXXXXXXXXX` format |

4. Restart the server (locally) or redeploy (on Render).

**Phone number format**: pastor phone numbers are stored in local
Philippine format (e.g. `0917 452 6631`) to match how the app was seeded.
Before sending, the app automatically converts that to the `+63...`
international format Twilio requires — no need to re-enter numbers with a
country code. If you enter a number with `+` already, it's used as-is.

**Regulatory note**: sending SMS to the Philippines (or any country) via
Twilio may require additional carrier registration or a local sender ID
depending on volume and use case — check Twilio's
[Philippines guidelines](https://www.twilio.com/en-us/guidelines/ph/sms)
before sending to real numbers at scale.

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
   Copy `.env.example` to `.env` and adjust values if needed — it's loaded
   automatically, no extra setup required. The project falls back to safe
   development defaults (including printing emails to the console instead
   of sending them) if you skip this step entirely.

5. **Apply migrations** — this creates `db.sqlite3` *and* seeds it with the
   demo data (the 3 budget line items, org settings, and the `treasurer`
   login) via a data migration, so the site looks right the first time you
   open it. Pastors start empty by design — see "Login & demo accounts"
   below.
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

## Deploying on Render

This project is pre-configured for Render: it uses `dj-database-url` (reads
a `DATABASE_URL` env var, falls back to local SQLite), `whitenoise` (serves
static files without a separate web server), and `gunicorn` (the
production server), plus `build.sh` which Render runs automatically.

### 1. Push to GitHub

```bash
git init
git add .
git commit -m "Ready for Render deployment"
git branch -M main
git remote add origin <your-empty-repo-url>
git push -u origin main
```

### 2. Create the database on Render

1. Render dashboard → **New** → **PostgreSQL**.
2. Give it a name, pick the free tier, create it.
3. Once it's up, copy its **Internal Database URL** — you'll paste it into
   the web service's environment variables in the next step.

### 3. Create the web service

1. Render dashboard → **New** → **Web Service** → connect your GitHub repo.
2. Settings:
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn config.wsgi:application`
3. Add these **Environment Variables**:

   | Key | Value |
   |---|---|
   | `DJANGO_SECRET_KEY` | a long random string (generate one below) |
   | `DJANGO_DEBUG` | `False` |
   | `DATABASE_URL` | the Internal Database URL from step 2 |
   | `EMAIL_HOST_USER` | *(optional, local dev only — Gmail SMTP is blocked on Render)* |
   | `EMAIL_HOST_PASSWORD` | *(optional, local dev only)* |
   | `BREVO_API_KEY` | *(optional)* see "Sending real emails" below — this is the one that actually works on Render |
   | `DEFAULT_FROM_EMAIL` | *(required if using Brevo)* your verified Sender address |
   | `TWILIO_ACCOUNT_SID` | *(optional)* see "Sending real SMS" below |
   | `TWILIO_AUTH_TOKEN` | *(optional)* see "Sending real SMS" below |
   | `TWILIO_FROM_NUMBER` | *(optional)* see "Sending real SMS" below |

   Render automatically provides `RENDER_EXTERNAL_HOSTNAME`, which
   `settings.py` already trusts for `ALLOWED_HOSTS`/`CSRF_TRUSTED_ORIGINS` —
   you don't need to set that one yourself.

   To generate a secret key, run this locally:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(50))"
   ```

4. Click **Create Web Service**. Render will run `build.sh` (installs
   dependencies, collects static files, runs migrations) and then start
   the app with gunicorn.

### 4. First-login setup

Once it's live at `https://<your-app>.onrender.com`:

1. Log in as `treasurer` / `treasurer123`.
2. Go to **Settings** and/or use Render's **Shell** tab
   (`python manage.py changepassword treasurer`) to change that password
   immediately — it's public in this README.
3. Add your real pastors from the **Pastors** page and create their logins
   from there.

### Redeploying after changes

Push to your GitHub branch — Render auto-deploys on every push (re-runs
`build.sh`, so migrations run automatically too).

### Alternative hosts

The same `build.sh` / `gunicorn` / `dj-database-url` / `whitenoise` setup
works with minimal changes on Railway, Fly.io, or a plain VPS — the main
difference is how each platform wants you to supply `DATABASE_URL` and
run the build/start commands.

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
