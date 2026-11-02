"""Read Google Tasks, group incomplete tasks, and open a local text report."""

import argparse
from datetime import date, timedelta
from pathlib import Path
import subprocess
import sys
from urllib.parse import parse_qs, urlsplit
import secrets
from getpass import getpass

ROOT = Path(__file__).resolve().parent
SCOPE = ["https://www.googleapis.com/auth/tasks.readonly"]


def pages(resource, **params):
    """Google returns results in pages; keep going until there are no more."""
    while True:
        response = resource.list(**params).execute()
        yield from response.get("items", [])
        token = response.get("nextPageToken")
        if not token:
            break
        params["pageToken"] = token


def fetch_tasks(service):
    tasks = []
    for tasklist in pages(service.tasklists(), maxResults=100):
        for task in pages(service.tasks(), tasklist=tasklist["id"],
                          maxResults=100, showCompleted=False,
                          showDeleted=False, showAssigned=True):
            if task.get("status") == "needsAction" and not task.get("deleted"):
                tasks.append({**task, "list_name": tasklist.get("title", "Untitled list")})
    return tasks


def one_line(text):
    return " ".join(text.split())


def format_report(tasks, today):
    groups = {name: [] for name in ("OVERDUE", "DUE TODAY", "UPCOMING", "NO DUE DATE")}
    for task in tasks:
        if task.get("status") != "needsAction" or task.get("deleted"):
            continue
        # Google Tasks dates are calendar dates, not times to convert to local time.
        due = date.fromisoformat(task["due"][:10]) if task.get("due") else None
        group = ("NO DUE DATE" if due is None else "OVERDUE" if due < today
                 else "DUE TODAY" if due == today else "UPCOMING")
        groups[group].append((due, task))
    count = sum(len(items) for items in groups.values())
    lines = [f"MY TASKS - {today:%d %B %Y}",
             f"All lists | {count} incomplete tasks", ""]
    if not count:
        lines.append("No incomplete tasks found.")
    else:
        for name, items in groups.items():
            lines.append(f"{name} ({len(items)})")
            for due, task in sorted(items, key=lambda item: (
                    item[0] or date.max, item[1].get("list_name", "").casefold(),
                    item[1].get("title", "").casefold())):
                title = one_line(task.get("title", "")) or "(Untitled task)"
                list_name = one_line(task.get("list_name", "Untitled list"))
                suffix = f" - due {due:%d %b %Y}" if due else ""
                lines.append(f"[ ] {title} [{list_name}]{suffix}")
            if not items:
                lines.append("None")
            lines.append("")
    return "\n".join(lines) + "\n"


def connect(credentials_path, token_path, manual_login=False):
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPE)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    "Google setup needed: save your Desktop app OAuth download as "
                    ".private/credentials.json in this repo. See README.md.")
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPE)
            if manual_login:
                flow.redirect_uri = "http://localhost:51076/"
                flow.autogenerate_code_verifier = True
                login_url, state = flow.authorization_url(prompt="consent")
                print(f"Open this Google sign-in link:\n{login_url}", flush=True)
                print("After approval, the localhost page may fail to load. "
                      "Copy its full address and paste it below.", flush=True)
                callback = getpass("Return address (hidden): ")
                parsed = urlsplit(callback.strip())
                params = parse_qs(parsed.query)
                if (parsed.scheme != "http" or parsed.netloc != "localhost:51076"
                        or parsed.path != "/"
                        or not secrets.compare_digest(params.get("state", [""])[0], state)):
                    raise ValueError("The return address does not match this login attempt.")
                if "error" in params or not params.get("code"):
                    raise ValueError("Google did not return an authorization code.")
                flow.fetch_token(code=params["code"][0])
                creds = flow.credentials
            else:
                creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json(), encoding="utf-8")
    return build("tasks", "v1", credentials=creds, cache_discovery=False)


def demo_tasks(today):
    return [
        {"title": "Book dentist (example)", "list_name": "Personal", "status": "needsAction",
         "due": (today - timedelta(days=3)).isoformat() + "T00:00:00.000Z"},
        {"title": "Submit expenses (example)", "list_name": "Work", "status": "needsAction",
         "due": today.isoformat() + "T00:00:00.000Z"},
        {"title": "Renew membership (example)", "list_name": "Personal", "status": "needsAction",
         "due": (today + timedelta(days=4)).isoformat() + "T00:00:00.000Z"},
        {"title": "Sort spare room (example)", "list_name": "Home", "status": "needsAction"},
    ]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--demo", action="store_true", help="Use fictional tasks; no Google login")
    parser.add_argument("--no-open", action="store_true", help="Save without opening Notepad")
    parser.add_argument("--manual-login", action="store_true",
                        help="Paste Google's return address if the local callback cannot connect")
    args = parser.parse_args()
    today = date.today()
    try:
        tasks = demo_tasks(today) if args.demo else fetch_tasks(connect(
            ROOT / ".private" / "credentials.json", ROOT / ".private" / "token.json",
            manual_login=args.manual_login))
        report = format_report(tasks, today)
        if args.demo:
            report = "DEMO ONLY - fictional tasks\n\n" + report
        output = ROOT / "outputs" / ("demo-tasks.txt" if args.demo else "my-tasks.txt")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(report, encoding="utf-8-sig")
        print(f"Saved: {output}")
        if not args.no_open:
            subprocess.Popen(["notepad.exe", str(output)])
        return 0
    except Exception as error:
        # Do not replace the last successful report if fetching tasks fails.
        print(f"Could not create task report: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
