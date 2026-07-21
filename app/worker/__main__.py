import asyncio
import logging

from app.core.log import setup_logging

logger = logging.getLogger(__name__)


async def main():
    setup_logging()
    logger.info("Worker starting")

    from app.worker.consumer import run_worker
    await run_worker()


if __name__ == "__main__":
    asyncio.run(main())
