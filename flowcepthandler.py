import json
# academy => flowcept log handler

# take a couple of relevant academy extras messages and turn them into flowcept API calls.
# see https://flowcept.readthedocs.io/en/latest/prov_capture.html#custom-task-creation-fully-customizable
# need then to keep an array of active flowcept task objects, every time i see an action
# start I create an object and send a start message, and every tie i see an action end,
# i create an object and send an end message.

import logging
import sys
import uuid

from academy.logging.configs.base import LogConfig

from flowcept import Flowcept, FlowceptTask


class FlowceptLogging(LogConfig):

    def __init__(self):
        super().__init__()
        #self.workflow_id = uuid.uuid4()

    def init_logging(self):
        print("**** FlowceptLogging init_logging")
        flowcept = Flowcept()
        flowcept.start()

        h = FlowceptHandler()
        h.setLevel(logging.DEBUG)
        action_logger = logging.getLogger("academy")
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
      if "academy.action_tag" in record.__dict__ \
         and "academy.action_state" in record.__dict__:
          action_invocation = record.__dict__["academy.action_tag"]
          print("*" * 79)
          sys.stdout.flush()
          match record.__dict__["academy.action_state"]:
            case "start":
              assert action_invocation not in self.flowcept_tasks

              agent_id = str(record.__dict__['academy.agent_id'].uid)
              args = record.__dict__.get("academy.action_args")
              kwargs = record.__dict__.get("academy.action_kwargs")
              used = {}
              if args:
                  used["args"] = args
              if kwargs:
                  used.update(kwargs)

              used = used or None
              ft = FlowceptTask(task_id = str(action_invocation),
                                activity_id = record.__dict__["academy.action"],
                                used=used,
                                agent_id=agent_id)
              self.flowcept_tasks[action_invocation] = ft
            case "success":
              ft = self.flowcept_tasks[action_invocation]
              result = record.__dict__.get("academy.result")
              def json_safe(obj):
                try:
                    obj = vars(obj)
                except TypeError:
                    pass

                return json.loads(json.dumps(obj, default=str))

              safe_result = json_safe(result)
              ft.end(generated=safe_result)
              del self.flowcept_tasks[action_invocation]
            case x:
              # TODO: add handlers for 'academy.action_state': 'exception', 'canceled'
              print(f"+++++++++++ Unknown action state: {x}")
              sys.stdout.flush()

