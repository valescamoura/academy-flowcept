academy observability / flowcept prototype
==========================================

Get a reasonable commit from the academy log config prototype branch:

```
pip install git+https://github.com/academy-agents/academy@66b3ac795ce0ea82a57ac2db790a18f3ea6b93c0
```

Get flowcept

```
pip install flowcept==0.9.20
```

Get parsl (because this uses Parsl-based executors to add some process complexity)

```
pip install parsl==2026.02.16
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

Look in `flowcept_buffer.jsonl` for flowcept logs.

Optionally, run:

`flowcept --generate-report --input-path flowcept_buffer.jsonl`

And open the `PROVENANCE_CARD.md`

