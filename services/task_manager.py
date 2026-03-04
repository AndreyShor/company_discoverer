from __future__ import annotations

import asyncio
import json
import uuid
from enum import StrEnum
from typing import Optional

from core.cache import get_redis
from core.logging import get_logger

logger = get_logger(__name__)

_TASK_KEY_PREFIX = "task:"
_TASK_TTL_SECONDS = 3600


class TaskStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskManager:
    """Redis-backed distributed task queue with cancellation support."""

    async def create_task(self, task_type: str, payload: dict) -> str:
        """Enqueue a new task and return its task_id."""
        task_id = str(uuid.uuid4())
        state = {
            "task_id": task_id,
            "task_type": task_type,
            "status": TaskStatus.PENDING,
            "payload": payload,
            "result": None,
            "error": None,
        }
        redis = get_redis()
        await redis.set(
            f"{_TASK_KEY_PREFIX}{task_id}",
            json.dumps(state),
            ex=_TASK_TTL_SECONDS,
        )
        logger.info("task_created", task_id=task_id, task_type=task_type)
        return task_id

    async def get_task(self, task_id: str) -> Optional[dict]:
        """Retrieve current task state by task_id."""
        redis = get_redis()
        raw = await redis.get(f"{_TASK_KEY_PREFIX}{task_id}")
        if raw is None:
            return None
        return json.loads(raw)

    async def update_task(self, task_id: str, **kwargs) -> None:
        """Partially update task state fields."""
        state = await self.get_task(task_id)
        if state is None:
            return
        state.update(kwargs)
        redis = get_redis()
        await redis.set(
            f"{_TASK_KEY_PREFIX}{task_id}",
            json.dumps(state),
            ex=_TASK_TTL_SECONDS,
        )

    async def cancel_task(self, task_id: str) -> bool:
        """Request cancellation of a task. Returns True if the task existed."""
        state = await self.get_task(task_id)
        if state is None:
            return False
        if state["status"] in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
            return False
        await self.update_task(task_id, status=TaskStatus.CANCELLED)
        logger.info("task_cancelled", task_id=task_id)
        return True

    async def is_cancelled(self, task_id: str) -> bool:
        """Check whether a task has been requested to cancel."""
        state = await self.get_task(task_id)
        return state is not None and state["status"] == TaskStatus.CANCELLED


task_manager = TaskManager()
