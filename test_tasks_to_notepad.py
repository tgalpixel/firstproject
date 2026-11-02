import unittest
from datetime import date
from types import SimpleNamespace
from unittest.mock import Mock

from tasks_to_notepad import fetch_tasks, format_report


class TasksTests(unittest.TestCase):
    def test_groups_dates_filters_completed_and_keeps_list_names(self):
        tasks = [
            {"title": "Later", "due": "2026-11-05T00:00:00Z"},
            {"title": "Today", "due": "2026-11-02T00:00:00Z"},
            {"title": "Old", "due": "2026-10-30T00:00:00Z"},
            {"title": "Undated"},
            {"title": "Done", "status": "completed"},
            {"title": "Deleted", "deleted": True},
        ]
        tasks = [{"status": "needsAction", "list_name": "Home", **t} for t in tasks]
        report = format_report(tasks, date(2026, 11, 2))
        self.assertIn("4 incomplete tasks", report)
        self.assertLess(report.index("Old [Home]"), report.index("Today [Home]"))
        self.assertLess(report.index("Today [Home]"), report.index("Later [Home]"))
        self.assertLess(report.index("Later [Home]"), report.index("Undated [Home]"))
        self.assertNotIn("Done", report)
        self.assertNotIn("Deleted", report)

    def test_empty_account(self):
        self.assertIn("No incomplete tasks found.", format_report([], date(2026, 11, 2)))

    def test_fetches_every_list_and_task_page_including_assigned(self):
        lists, tasks = Mock(), Mock()
        lists.list.return_value.execute.side_effect = [
            {"items": [{"id": "a", "title": "Home"}], "nextPageToken": "lists2"},
            {"items": [{"id": "b", "title": "Work"}]},
        ]
        tasks.list.return_value.execute.side_effect = [
            {"items": [{"title": "One", "status": "needsAction"}], "nextPageToken": "tasks2"},
            {"items": [{"title": "Two", "status": "needsAction"}]},
            {"items": [{"title": "Three", "status": "needsAction"}]},
        ]
        service = SimpleNamespace(tasklists=lambda: lists, tasks=lambda: tasks)
        result = fetch_tasks(service)
        self.assertEqual([t["list_name"] for t in result], ["Home", "Home", "Work"])
        self.assertEqual(lists.list.call_args_list[1].kwargs["pageToken"], "lists2")
        self.assertEqual(tasks.list.call_args_list[1].kwargs["pageToken"], "tasks2")
        self.assertTrue(tasks.list.call_args_list[0].kwargs["showAssigned"])
        self.assertFalse(tasks.list.call_args_list[0].kwargs["showCompleted"])


if __name__ == "__main__":
    unittest.main()
