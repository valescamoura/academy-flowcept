academy observability / flowcept prototype
==========================================

Get a recent version of Academy: (for example, this version on the `main` branch)

```
pip install git+https://github.com/academy-agents/academy@1c9dd5bbe030e562101a30dd4dfa1b5b0dffff4d
```

Get flowcept

```
pip install flowcept==0.9.20
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

Look in `flowcept_buffer.jsonl` for flowcept logs.

Optionally, run:

`flowcept --generate-report --input-path flowcept_buffer.jsonl`

And open the `PROVENANCE_CARD.md`

