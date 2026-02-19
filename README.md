academy observability / flowcept prototype
==========================================

Get a reasonable commit from the academy log config prototype branch:

```
pip install git+https://github.com/academy-agents/academy@c2ad965404f45a2c7918fd457e460b786800113b
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
export PYTHONPATH=$(pwd)
python3 fibiterate7.py
```

Look in `flowcept_buffer.jsonl` for flowcept logs.
