"""Academy logging integration for Flowcept provenance capture."""

# academy => flowcept log handler
# take a couple of relevant academy extras messages and turn them into flowcept API calls.
# see https://flowcept.readthedocs.io/en/latest/prov_capture.html#custom-task-creation-fully-customizable
# need then to keep an array of active flowcept task objects, every time i see an action
# start I create an object and send a start message, and every tie i see an action end,
# i create an object and send an end message.

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from typing import Any

from academy.logging.configs.base import LogConfig
from flowcept import AgentObject, Flowcept, FlowceptTask
from flowcept.commons.vocabulary import Status


def _json_safe(value: Any) -> Any:
    """Return a JSON-compatible representation without leaking AgentId wrappers."""
    if hasattr(value, "uid"):
        return str(value.uid)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    try:
        return json.loads(json.dumps(value, default=str))
    except (TypeError, ValueError):
        return str(value)


def _entity_id(entity: Any) -> str | None:
    uid = getattr(entity, "uid", None)
    return str(uid) if uid is not None else None


def _entity_name(entity: Any) -> str | None:
    name = getattr(entity, "name", None)
    return str(name) if name else None


def _is_agent(entity: Any) -> bool:
    return getattr(entity, "role", None) == "agent"


@dataclass
class _PendingAction:
    activity_id: str
    used: dict[str, Any] | None
    started_at: float
    destination: Any = None
    source: Any = None
    task: FlowceptTask | None = None


class FlowceptLogging(LogConfig):
    """Install a handler that converts Academy action events into Flowcept tasks."""

    def __init__(
        self,
        *,
        workflow_id: str | None = None,
        campaign_id: str | None = None,
        workflow_name: str | None = None,
        workflow_subtype: str | None = None,
        start_persistence: bool = True,
        save_workflow: bool = True,
    ) -> None:
        super().__init__()
        self.workflow_id = workflow_id or os.getenv("FLOWCEPT_WORKFLOW_ID")
        self.campaign_id = campaign_id or os.getenv("FLOWCEPT_CAMPAIGN_ID")
        self.workflow_name = workflow_name or os.getenv("FLOWCEPT_WORKFLOW_NAME")
        self.workflow_subtype = workflow_subtype or os.getenv("FLOWCEPT_WORKFLOW_SUBTYPE")
        self.start_persistence = start_persistence
        self.save_workflow = save_workflow

    def init_logging(self):
        flowcept = Flowcept(
            workflow_id=self.workflow_id,
            campaign_id=self.campaign_id,
            workflow_name=self.workflow_name,
            workflow_subtype=self.workflow_subtype,
            start_persistence=self.start_persistence,
            save_workflow=self.save_workflow,
        )
        flowcept.start()

        handler = FlowceptHandler(
            workflow_id=Flowcept.current_workflow_id,
            campaign_id=Flowcept.campaign_id,
        )
        handler.setLevel(logging.DEBUG)
        action_logger = logging.getLogger("academy")
        action_logger.addHandler(handler)
        action_logger.setLevel(min(action_logger.level, handler.level))

        def uninit() -> None:
            action_logger.removeHandler(handler)
            handler.close_unfinished()
            handler.close()
            flowcept.stop()

        return uninit


class FlowceptHandler(logging.Handler):
    """Correlate Academy action lifecycle records by ``academy.action_tag``."""

    def __init__(self, workflow_id: str | None = None, campaign_id: str | None = None) -> None:
        super().__init__()
        self.workflow_id = workflow_id
        self.campaign_id = campaign_id
        self.flowcept_tasks: dict[str, FlowceptTask] = {}
        self.pending_actions: dict[str, _PendingAction] = {}
        self._registered_agents: set[str] = set()

    def emit(self, record: logging.LogRecord) -> None:
        try:
            data = record.__dict__
            action_tag = data.get("academy.action_tag")
            state = data.get("academy.action_state")
            if action_tag is None or state is None or str(state).startswith("execute_"):
                return

            action_id = str(action_tag)
            if state == "start":
                self._start(action_id, record)
            elif state == "sending":
                self._sending(action_id, record)
            elif state == "success":
                self._finish(action_id, record, Status.FINISHED)
            elif state in {"exception", "cancelled", "canceled"}:
                self._finish(action_id, record, Status.ERROR)
        except Exception:
            self.handleError(record)

    def _start(self, action_id: str, record: logging.LogRecord) -> None:
        data = record.__dict__
        activity_id = str(data.get("academy.action", "unknown_action"))
        args = data.get("academy.action_args")
        kwargs = data.get("academy.action_kwargs")
        used: dict[str, Any] = {}
        if args:
            used["args"] = _json_safe(args)
        if kwargs:
            used.update(_json_safe(kwargs))

        destination = data.get("academy.agent_id")
        self.pending_actions[action_id] = _PendingAction(
            activity_id=activity_id,
            used=used or None,
            started_at=record.created,
            destination=destination,
        )
        self._register_agent(destination)

    def _sending(self, action_id: str, record: logging.LogRecord) -> None:
        pending = self.pending_actions.get(action_id)
        if pending is None:
            return
        data = record.__dict__
        pending.source = data.get("academy.src")
        pending.destination = data.get("academy.dest") or pending.destination
        self._register_agent(pending.source)
        self._register_agent(pending.destination)
        self._ensure_task(action_id, pending)

    def _ensure_task(self, action_id: str, pending: _PendingAction) -> FlowceptTask:
        if pending.task is None:
            source_id = _entity_id(pending.source) if _is_agent(pending.source) else None
            pending.task = FlowceptTask(
                task_id=action_id,
                workflow_id=self.workflow_id,
                campaign_id=self.campaign_id,
                activity_id=pending.activity_id,
                agent_id=_entity_id(pending.destination),
                source_agent_id=source_id,
                used=pending.used,
                subtype="academy_action",
                started_at=pending.started_at,
                custom_metadata={"framework": "academy", "capture_method": "event_log"},
            )
            self.flowcept_tasks[action_id] = pending.task
        return pending.task

    def _finish(self, action_id: str, record: logging.LogRecord, status: Status) -> None:
        pending = self.pending_actions.pop(action_id, None)
        if pending is None:
            return
        task = self._ensure_task(action_id, pending)
        if status == Status.FINISHED:
            result = _json_safe(record.__dict__.get("academy.result"))
            generated = result if isinstance(result, dict) else {"result": result}
            task.end(generated=generated, ended_at=record.created, status=status)
        else:
            error = record.getMessage() or str(record.__dict__.get("academy.exception", "Action failed"))
            task.end(ended_at=record.created, stderr=error, status=status)
        self.flowcept_tasks.pop(action_id, None)

    def _register_agent(self, entity: Any) -> None:
        if not _is_agent(entity):
            return
        agent_id = _entity_id(entity)
        if agent_id is None or agent_id in self._registered_agents:
            return
        agent = AgentObject(
            agent_id=agent_id,
            name=_entity_name(entity),
            workflow_id=self.workflow_id,
            campaign_id=self.campaign_id,
        )
        agent.extra_metadata = {"framework": "academy", "capture_method": "event_log"}
        agent.enrich()
        Flowcept.db.insert_or_update_agent(agent)
        self._registered_agents.add(agent_id)

    def close_unfinished(self) -> None:
        for action_id, pending in list(self.pending_actions.items()):
            task = self._ensure_task(action_id, pending)
            task.end(stderr="Logging stopped before the Academy action completed", status=Status.ERROR)
        self.pending_actions.clear()
        self.flowcept_tasks.clear()
