Tgalpixel | 2 November 2026 | This repo is the safe point for my first agent project.

# firstproject: Google Tasks to Notepad

Read incomplete tasks from **all** your Google Tasks lists and open a text report
in Notepad. Overdue tasks come first, then today's, upcoming, and undated tasks.
Each task shows its source list. Completed and deleted tasks are excluded.

This first milestone uses ordinary Python and Google's read-only Tasks API.
It does not change tasks or send email. Dates from Google Tasks contain a day,
not a due time; the report compares them with today's date on your laptop.

## Run locally

With Python 3.10 or newer installed, open PowerShell in this repository:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe tasks_to_notepad.py --demo
```

Demo mode uses clearly labelled fictional tasks and does not need Google access.
After completing the Google setup below, run with real tasks:

```powershell
.\.venv\Scripts\python.exe tasks_to_notepad.py
```

The report is saved to `outputs/my-tasks.txt` and opens in Notepad. Add `--no-open`
to save without opening it. A failed fetch leaves the previous report intact.
Demo output uses a separate file, `outputs/demo-tasks.txt`.

If the browser cannot reach the local sign-in callback, use:

```powershell
.\.venv\Scripts\python.exe tasks_to_notepad.py --manual-login
```

Open the printed Google sign-in link and approve access. The final localhost
page will fail to load in this mode. Immediately copy its full address into the
program's hidden terminal prompt. It checks that the address matches this login
attempt and exchanges the short-lived code over HTTPS. Treat the return address
as private. Once the login is saved, normal runs do not need this step.

## Connect your Google account (one-time setup)

1. Open https://console.cloud.google.com/ and create a project called
   **Tgalpixel Tasks**. Select that project.
2. In **APIs & Services > Library**, find **Google Tasks API** and enable it.
3. Open **Google Auth platform > Branding**, then **Get started** if prompted.
   Use **Tgalpixel Tasks** as the app name and your email for support/contact.
   For a personal Gmail account choose an **External** audience.
4. In **Audience**, keep the app in Testing and add your Google email as a test user.
5. In **Data Access**, add the scope
   `https://www.googleapis.com/auth/tasks.readonly`.
6. In **Clients > Create client**, choose **Desktop app**, name it
   **Tasks on my laptop**, and create it. Download its JSON file.
7. Create a `.private` folder in this repository. Place the download inside it,
   renamed to `credentials.json`.
8. Run the program without `--demo`. Sign in using the Google account whose tasks
   you want and approve read-only Tasks access in the browser.

The program stores its reusable Google login in `.private/token.json`.
The `.private` folder, generated reports, and Python environment are excluded
from Git. Keep the login files on your laptop; don't paste them into chat or GitHub.
Google may require another login while the OAuth app is in Testing. If access
expires or is revoked, delete `.private/token.json` and run again to sign in.

Google's setup reference:
https://developers.google.com/workspace/tasks/quickstart/python

## How it works

`connect` handles Google login. `pages` follows Google's next-page tokens so a
large list isn't cut short. `fetch_tasks` reads every list, including assigned
tasks exposed by the API. `format_report` groups and sorts the results.
`main` saves the text and opens Notepad. Subtasks appear as individual entries.

## Checks

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

Tests cover date grouping, completed/deleted filtering, empty results, and
pagination across both task lists and tasks. A real-account check requires
your Google OAuth setup and consent.
