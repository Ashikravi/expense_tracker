# Expense Tracker (Django)

A small personal expense tracker: add expenses, browse and filter them, and see this month's spending by category. Django + SQLite, server-rendered with plain HTML templates and no JavaScript needed.

## How to run

Requires Python 3.10+.

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000. The SQLite file `db.sqlite3` is created by `migrate`.

## Project layout

```
config/                 project settings and root urls
expenses/
  models.py             Expense model + Category choices
  forms.py              ExpenseForm (add) and FilterForm (list filters)
  views.py              list/add, edit and delete views, plus two small helpers (filters, monthly summary)
  urls.py
  migrations/0001_initial.py
  templates/expenses/     base.html, list.html, edit.html, confirm_delete.html
```

## Data model

One table, `Expense`: `title`, `amount_paise`, `category`, `spent_on`, `note`, `created_at`.

- **Amount is stored as integer paise**, not a float or `DecimalField`. SQLite has no real decimal type, so integers keep sums exact. The model exposes an `amount` property (a `Decimal` in rupees) for display.
- **Category is a `TextChoices` enum** (food, transport, bills, entertainment, shopping, health, other). The form dropdowns are built from it, so they can't drift from the model.
- `spent_on` (the date of the expense) is separate from `created_at` (when it was entered). `spent_on` and `category` are indexed because every filter and the monthly summary use them.
- Default ordering is `-spent_on, -id`, so the list is newest first and same-day ties are stable.

## How it works

- **Add**: a plain `Form` validates, then `save()` converts rupees to paise and creates the row. On success the view redirects (post/redirect/get), so refreshing doesn't resubmit, and active filters are kept.
- **List and filters**: filters are a GET form, so a filtered view is a shareable URL. Each filter is optional and they combine with AND.
- **Summary**: one grouped query (`values("category").annotate(Sum, Count)`) for the current calendar month, independent of the list filters.
- **Edit and delete**: edit reuses the same `ExpenseForm`, pre-filled from the saved expense, so it has identical validation to adding. Delete shows a confirmation page first, and only a POST removes the row, so a stray link or crawler can't delete anything.

## Edge cases handled

- Title blank, whitespace-only or over 100 chars; amount zero, negative, empty, more than 2 decimals or too large; unknown category; impossible date (e.g. 31 Feb). All rejected with an inline message and your input kept.
- `From` later than `To` shows an error instead of a misleading empty list. Either date can be used alone; both are inclusive.
- Garbage in the URL (`?date_from=abc`) shows a validation error rather than crashing.
- Title search is case-insensitive and `%` / `_` match literally.
- Empty states: no expenses at all, no matches for the filters, and no spending this month each have their own message.
- Templates auto-escape, so a title like `<b>x</b>` is shown as text.
- Editing or deleting an expense that no longer exists (e.g. deleted in another tab) shows a 404 page.
- Edit shows the same inline errors as add, and nothing is saved until the form is valid.

## Stack choices and tradeoffs

- **Django over FastAPI**: forms, validation, migrations, CSRF protection and templating are built in, so there's little custom code. The tradeoff is more boilerplate files for a small app.
- **Server-rendered templates, no JS**: fewer moving parts and nothing to keep in sync between a frontend and an API. The cost is a full page reload on each action, and a JSON API would need adding for any other client.
- **Plain `Form` instead of `ModelForm`**: the form takes rupees but the model stores paise, so a `ModelForm` would need extra conversion code. A plain form with a `save()` keeps that mapping in one place.
- **SQLite**: zero setup for a local app. The ORM means moving to Postgres later is a settings change.
- **Single view**: add form, summary and list live on one page, so one view is simplest. I'd split it if the page grew.

## Done vs skipped

**Done**: add, edit, delete (with a confirmation step), list (newest first, all fields), monthly summary with category breakdown, filters (category, date range, title), validation and empty states, migrations, README.

**Skipped, deliberately**
- Authentication, deployment: out of scope for a local app.
- Tests: out of scope. I smoke-tested add, validation, filters and summary with Django's test client. With more time I'd add proper `TestCase`s.
- Pagination: the list loads everything, which is fine for personal use.
- Browsing past months: the summary is always the current month, as the brief asks.

## Known rough edges

- No pagination, so thousands of rows would render slowly.
- After an edit or delete you land on the unfiltered list, not on the filters you had applied.
- Delete is permanent: there's no undo or soft-delete.
- Adding an expense reloads the page.
- SQLite's case-insensitive search only folds ASCII letters, so non-English titles may match case-sensitively.
- "This month" uses the server's clock and the `Asia/Kolkata` timezone set in settings.
- Categories are fixed in code; adding one means editing the model and creating a migration.
- Future-dated expenses are allowed, and only count towards the summary in their own month.
