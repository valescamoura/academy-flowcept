import logging
import types
import unittest
import uuid
from unittest.mock import patch

import flowcepthandler


class FakeEntity:
    def __init__(self, name, role="agent"):
        self.uid = uuid.uuid4()
        self.name = name
        self.role = role


class FakeTask:
    created = []

    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.ended = None
        self.__class__.created.append(self)

    def end(self, **kwargs):
        self.ended = kwargs


class FakeDB:
    def __init__(self):
        self.agents = []

    def insert_or_update_agent(self, agent):
        self.agents.append(agent)


def action_record(state, **extra):
    attributes = {
        "academy.action_tag": "action-1",
        "academy.action_state": state,
        **extra,
    }
    return logging.makeLogRecord(attributes)


class FlowceptHandlerTest(unittest.TestCase):
    def setUp(self):
        FakeTask.created.clear()
        self.db = FakeDB()
        self.fake_flowcept = types.SimpleNamespace(db=self.db)
        self.patches = (
            patch.object(flowcepthandler, "FlowceptTask", FakeTask),
            patch.object(flowcepthandler, "Flowcept", self.fake_flowcept),
        )
        for active_patch in self.patches:
            active_patch.start()
        self.addCleanup(lambda: [active_patch.stop() for active_patch in reversed(self.patches)])

    def test_records_source_and_destination_agents(self):
        source = FakeEntity("orchestrator")
        destination = FakeEntity("training-worker")
        handler = flowcepthandler.FlowceptHandler("workflow-1", "campaign-1")

        handler.emit(
            action_record(
                "start",
                **{
                    "academy.action": "train_config",
                    "academy.action_kwargs": {"config_id": "config-1"},
                    "academy.agent_id": destination,
                },
            )
        )
        handler.emit(
            action_record(
                "sending",
                **{"academy.src": source, "academy.dest": destination},
            )
        )
        handler.emit(action_record("success", **{"academy.result": {"accuracy": 0.9}}))

        task = FakeTask.created[0]
        self.assertEqual(task.kwargs["agent_id"], str(destination.uid))
        self.assertEqual(task.kwargs["source_agent_id"], str(source.uid))
        self.assertEqual(task.kwargs["subtype"], "academy_action")
        self.assertEqual(task.ended["generated"], {"accuracy": 0.9})
        self.assertEqual(
            {(agent.agent_id, agent.name) for agent in self.db.agents},
            {(str(source.uid), "orchestrator"), (str(destination.uid), "training-worker")},
        )

    def test_does_not_use_a_user_as_source_agent(self):
        user = FakeEntity("driver", role="user")
        destination = FakeEntity("orchestrator")
        handler = flowcepthandler.FlowceptHandler("workflow-1", "campaign-1")

        handler.emit(
            action_record(
                "start",
                **{"academy.action": "run", "academy.agent_id": destination},
            )
        )
        handler.emit(
            action_record(
                "sending",
                **{"academy.src": user, "academy.dest": destination},
            )
        )
        handler.emit(action_record("success", **{"academy.result": "done"}))

        self.assertIsNone(FakeTask.created[0].kwargs["source_agent_id"])
        self.assertEqual(FakeTask.created[0].ended["generated"], {"result": "done"})

if __name__ == "__main__":
    unittest.main()
