academy observability / flowcept prototype
==========================================

Get a reasonable commit from the academy log config prototype branch:

```
pip install git+https://github.com/academy-agents/academy@6d6b87be06525d359b984017521cc479f0cd5c6a
```

Get flowcept

```
pip install flowcept==0.9.20
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
