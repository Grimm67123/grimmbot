"""
Tests for scheduler.py — PersistentScheduler CRUD and scheduling logic.
"""

import os
import sys
import json
import pytest
from pathlib import Path
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytz

from scheduler import (
    SchedulerConfig, ScheduledTask, ScheduleType,
    PersistentScheduler, get_scheduler,
)


# ══════════════════════════════════════════════════════════════════════════════
# Fixtures
# ══════════════════════════════════════════════════════════════════════════════


@pytest.fixture
def sched_config(tmp_workspace):
    return SchedulerConfig(
        persistent=True,
        check_interval=1,
        data_dir=str(tmp_workspace["scheduler"]),
        timezone="UTC",
    )


@pytest.fixture
def scheduler(sched_config):
    return PersistentScheduler(sched_config)


# ══════════════════════════════════════════════════════════════════════════════
# ScheduledTask Dataclass
# ══════════════════════════════════════════════════════════════════════════════


class TestScheduledTask:
    def test_to_dict_and_back(self):
        task = ScheduledTask(
            id="test_001",
            prompt="Check email",
            schedule_type="once",
            schedule_value="2026-04-04T10:00:00",
            profile="default",
        )
        d = task.to_dict()
        restored = ScheduledTask.from_dict(d)
        assert restored.id == "test_001"
        assert restored.prompt == "Check email"
        assert restored.schedule_type == "once"

    def test_defaults(self):
        task = ScheduledTask(id="x", prompt="p", schedule_type="once", schedule_value="v")
        assert task.enabled is True
        assert task.run_count == 0
        assert task.profile == "default"


# ══════════════════════════════════════════════════════════════════════════════
# Schedule Creation
# ══════════════════════════════════════════════════════════════════════════════


class TestScheduleCreation:
    def test_schedule_once(self, scheduler):
        future = datetime.now(pytz.UTC) + timedelta(hours=1)
        task_id = scheduler.schedule_once("Do thing", future)
        assert task_id.startswith("once_")
        assert task_id in scheduler.tasks

    def test_schedule_daily(self, scheduler):
        task_id = scheduler.schedule_daily("Morning check", 8, 30)
        assert task_id.startswith("daily_")
        task = scheduler.tasks[task_id]
        assert task.schedule_value == "08:30"

    def test_schedule_interval(self, scheduler):
        task_id = scheduler.schedule_interval("Check status", 15)
        assert task_id.startswith("interval_")
        task = scheduler.tasks[task_id]
        assert task.schedule_value == "15"

    def test_schedule_with_tags(self, scheduler):
        future = datetime.now(pytz.UTC) + timedelta(hours=1)
        task_id = scheduler.schedule_once("Tagged", future, tags=["important", "email"])
        task = scheduler.tasks[task_id]
        assert "important" in task.tags


# ══════════════════════════════════════════════════════════════════════════════
# Task Management
# ══════════════════════════════════════════════════════════════════════════════


class TestTaskManagement:
    def test_list_tasks(self, scheduler):
        future = datetime.now(pytz.UTC) + timedelta(hours=1)
        scheduler.schedule_once("A", future)
        scheduler.schedule_daily("B", 9, 0)
        tasks = scheduler.list_tasks()
        assert len(tasks) == 2

    def test_cancel_task(self, scheduler):
        future = datetime.now(pytz.UTC) + timedelta(hours=1)
        task_id = scheduler.schedule_once("Cancel me", future)
        assert scheduler.cancel(task_id) is True
        assert task_id not in scheduler.tasks

    def test_cancel_nonexistent(self, scheduler):
        assert scheduler.cancel("fake_id") is False

    def test_get_task(self, scheduler):
        future = datetime.now(pytz.UTC) + timedelta(hours=1)
        task_id = scheduler.schedule_once("Get me", future)
        task = scheduler.get_task(task_id)
        assert task is not None
        assert task.prompt == "Get me"

    def test_get_task_nonexistent(self, scheduler):
        assert scheduler.get_task("nope") is None

    def test_stats(self, scheduler):
        future = datetime.now(pytz.UTC) + timedelta(hours=1)
        scheduler.schedule_once("A", future)
        stats = scheduler.stats()
        assert stats["total_tasks"] == 1
        assert stats["enabled_tasks"] == 1


# ══════════════════════════════════════════════════════════════════════════════
# _is_due Logic
# ══════════════════════════════════════════════════════════════════════════════


class TestIsDue:
    def test_once_not_yet_due(self, scheduler):
        future = datetime.now(pytz.UTC) + timedelta(hours=1)
        task_id = scheduler.schedule_once("Future", future)
        task = scheduler.tasks[task_id]
        now = datetime.now(pytz.UTC)
        assert scheduler._is_due(task, now) is False

    def test_once_is_due(self, scheduler):
        past = datetime.now(pytz.UTC) - timedelta(minutes=5)
        task_id = scheduler.schedule_once("Past", past)
        task = scheduler.tasks[task_id]
        now = datetime.now(pytz.UTC)
        assert scheduler._is_due(task, now) is True

    def test_daily_is_due(self, scheduler):
        now = datetime.now(pytz.UTC)
        task_id = scheduler.schedule_daily("Now-ish", now.hour, now.minute)
        task = scheduler.tasks[task_id]
        assert scheduler._is_due(task, now) is True

    def test_daily_already_ran_today(self, scheduler):
        now = datetime.now(pytz.UTC)
        task_id = scheduler.schedule_daily("Daily", now.hour, now.minute)
        task = scheduler.tasks[task_id]
        task.last_run = now.isoformat()
        assert scheduler._is_due(task, now) is False

    def test_interval_first_run(self, scheduler):
        task_id = scheduler.schedule_interval("Interval", 30)
        task = scheduler.tasks[task_id]
        now = datetime.now(pytz.UTC)
        assert scheduler._is_due(task, now) is True  # no last_run → due

    def test_interval_not_yet_due(self, scheduler):
        task_id = scheduler.schedule_interval("Interval", 30)
        task = scheduler.tasks[task_id]
        task.last_run = datetime.now(pytz.UTC).isoformat()
        now = datetime.now(pytz.UTC)
        assert scheduler._is_due(task, now) is False  # just ran

    def test_interval_is_due_after_elapsed(self, scheduler):
        task_id = scheduler.schedule_interval("Interval", 5)
        task = scheduler.tasks[task_id]
        task.last_run = (datetime.now(pytz.UTC) - timedelta(minutes=10)).isoformat()
        now = datetime.now(pytz.UTC)
        assert scheduler._is_due(task, now) is True

    def test_disabled_task_never_due(self, scheduler):
        past = datetime.now(pytz.UTC) - timedelta(minutes=5)
        task_id = scheduler.schedule_once("Disabled", past)
        task = scheduler.tasks[task_id]
        task.enabled = False
        now = datetime.now(pytz.UTC)
        assert scheduler._is_due(task, now) is False


# ══════════════════════════════════════════════════════════════════════════════
# _check_and_run
# ══════════════════════════════════════════════════════════════════════════════


class TestCheckAndRun:
    def test_callback_fired_for_due_task(self, scheduler):
        past = datetime.now(pytz.UTC) - timedelta(minutes=1)
        scheduler.schedule_once("Fire callback", past)
        results = []
        scheduler.add_callback(lambda task: results.append(task.prompt))

        scheduler._check_and_run()
        assert "Fire callback" in results

    def test_once_task_removed_after_execution(self, scheduler):
        past = datetime.now(pytz.UTC) - timedelta(minutes=1)
        task_id = scheduler.schedule_once("Remove me", past)
        scheduler.add_callback(lambda task: None)

        scheduler._check_and_run()
        assert task_id not in scheduler.tasks

    def test_daily_task_not_removed(self, scheduler):
        now = datetime.now(pytz.UTC)
        task_id = scheduler.schedule_daily("Keep me", now.hour, now.minute)
        scheduler.add_callback(lambda task: None)

        scheduler._check_and_run()
        assert task_id in scheduler.tasks

    def test_run_count_incremented(self, scheduler):
        past = datetime.now(pytz.UTC) - timedelta(minutes=1)
        task_id = scheduler.schedule_interval("Count me", 1)
        task = scheduler.tasks[task_id]
        task.last_run = (datetime.now(pytz.UTC) - timedelta(minutes=5)).isoformat()
        scheduler.add_callback(lambda task: None)

        scheduler._check_and_run()
        assert task.run_count == 1


# ══════════════════════════════════════════════════════════════════════════════
# Persistence
# ══════════════════════════════════════════════════════════════════════════════


class TestSchedulerPersistence:
    def test_save_and_load(self, sched_config):
        s1 = PersistentScheduler(sched_config)
        future = datetime.now(pytz.UTC) + timedelta(hours=2)
        s1.schedule_once("Persist me", future)
        del s1

        s2 = PersistentScheduler(sched_config)
        assert len(s2.tasks) == 1
        task = list(s2.tasks.values())[0]
        assert task.prompt == "Persist me"

    def test_non_persistent_no_save(self, tmp_workspace):
        config = SchedulerConfig(
            persistent=False,
            data_dir=str(tmp_workspace["scheduler"]),
            timezone="UTC",
        )
        s = PersistentScheduler(config)
        future = datetime.now(pytz.UTC) + timedelta(hours=1)
        s.schedule_once("No save", future)
        data_file = Path(tmp_workspace["scheduler"]) / "scheduled_tasks.json"
        assert not data_file.exists()


# ══════════════════════════════════════════════════════════════════════════════
# Start / Stop
# ══════════════════════════════════════════════════════════════════════════════


class TestStartStop:
    def test_start_and_stop(self, scheduler):
        scheduler.start()
        assert scheduler._running is True
        scheduler.stop()
        assert scheduler._running is False

    def test_start_idempotent(self, scheduler):
        scheduler.start()
        scheduler.start()  # should not crash
        assert scheduler._running is True
        scheduler.stop()
