### for feb 2026 observability demo

### ==== pretend this bit is in the academy standard library ==== ###

import asyncio
import os
from academy.agent import Agent, action
from academy.manager import Manager
from academy.exchange import LocalExchangeFactory, RedisExchangeFactory
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

from parsl.concurrent import ParslPoolExecutor
from parsl.config import Config

from fibiterate7lib import FibonacciLauncher, IteratorShim

from flowcepthandler import FlowceptLogging

from academy.logging import log_context

import logging
logger = logging.getLogger(__name__)

async def main():

  from academy.logging.configs.console import ConsoleLogging
  from academy.logging.configs.multi import MultiLogging

  lc = FlowceptLogging()

  # initialize logging locally, until the end of the process
  with log_context(MultiLogging([lc, ConsoleLogging(level=logging.DEBUG, extra=2)])):

   logger.info(f"start, main process is pid {os.getpid()}")

   from parsl.tests.configs.htex_local_alternate import fresh_config
   with ParslPoolExecutor(fresh_config()) as pe:

    async with await Manager.from_exchange_factory(
       factory=RedisExchangeFactory(hostname='localhost', port=6379),
        executors=pe) as m:
     logger.info(f"got manager {m!r}")
     a = FibonacciLauncher()
     ah = await m.launch(a, log_config=lc)

     iteratorh = await ah.calc_fibs(0, 1)
     assert iteratorh is not None
     logger.info(f"got iterator handle {iteratorh}")

     await iteratorh.ping()

     iterator_shim = IteratorShim(iteratorh)

     async for n in iterator_shim:
       logger.info(f"Iterator returned: {n}")
       print("Console iterated result: ", n)
       await asyncio.sleep(0.5)

   logger.info("end")


if __name__ == "__main__":
    asyncio.run(main())
