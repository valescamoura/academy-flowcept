# Academy Flowcept

Logging integration that converts Academy action lifecycle events into Flowcept
tasks. Each action is stored with subtype `academy_action`, its destination
`agent_id`, and its `source_agent_id` when another Academy agent invoked it.
The handler also creates Flowcept `AgentObject` records for observed agents.

Get a recent version of Academy: (for example, this version on the `main` branch)

```
pip install git+https://github.com/academy-agents/academy@1c9dd5bbe030e562101a30dd4dfa1b5b0dffff4d
```

Get the Flowcept version with agent provenance support:

```
pip install 'flowcept[extras] @ git+https://github.com/ORNL/flowcept@fc_ui'
```

Get parsl (because this uses Parsl-based executors to add some process complexity)

```
pip install 'parsl[monitoring]==2026.04.27'
```

Get redis (because this uses the redis-based exchange)

```
apt install redis-server
```

Run redis server

```
redis-server &
```

Run demo - this is a script that runs agent based fibonacci generation inside a Parsl-based agent, so that there are multiple processes and agents involved.

```
python3 fibiterate7.py
```

For distributed runs, pass the same `workflow_id` and `campaign_id` to every
`FlowceptLogging` instance. Only the driver process should use
`start_persistence=True` and `save_workflow=True`; worker processes should set
both options to `False`.

Optionally, run:

`flowcept --generate-report --input-path flowcept_buffer.jsonl`

And open the `PROVENANCE_CARD.md`
