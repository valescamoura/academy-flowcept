
# academy => flowcept log handler

# take a couple of relevant academy extras messages and turn them into flowcept API calls.
# see https://flowcept.readthedocs.io/en/latest/prov_capture.html#custom-task-creation-fully-customizable
# need then to keep an array of active flowcept task objects, every time i see an action
# start I create an object and send a start message, and every tie i see an action end,
# i create an object and send an end message.

import logging
import uuid

from academy.logging import LogConfig

from flowcept import Flowcept, FlowceptTask

class FlowceptLogging(LogConfig):

    def __init__(self):
        super().__init__()
        self.workflow_id = uuid.uuid4()

    def init_logging(self):

        flowcept = Flowcept(workflow_name=str(self.workflow_id))
        flowcept.start()

        h = FlowceptHandler()
        h.setLevel(logging.DEBUG)
        action_logger = logging.getLogger("academy.handle")
        action_logger.addHandler(h)
        action_logger.level = min(action_logger.level, h.level)

        def uninit():
            flowcept.stop()

        return uninit

class FlowceptHandler(logging.Handler):

  def __init__(self):
      super().__init__()
      self.flowcept_tasks: dict[str, FlowceptTask] = {}

  def emit(self, record):
      if "academy.action_invocation" in record.__dict__ \
         and "academy.action_state" in record.__dict__:
          action_invocation = record.__dict__["academy.action_invocation"]
          print("*" * 79)
          match record.__dict__["academy.action_state"]:
            case "start":
              assert action_invocation not in self.flowcept_tasks
              ft = FlowceptTask(task_id = action_invocation,
                                activity_id = record.__dict__["academy.action"])
              self.flowcept_tasks[action_invocation] = ft
            case "success":
              ft = self.flowcept_tasks[action_invocation]
              ft.end()
              del self.flowcept_tasks[action_invocation]

