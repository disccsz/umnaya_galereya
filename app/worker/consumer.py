import asyncio
import json
import logging
import signal

from aiokafka import AIOKafkaConsumer
from aiokafka.errors import KafkaConnectionError

from app.core.config import settings
from app.worker.processor import process_message

logger = logging.getLogger(__name__)

TOPIC_PHOTO_UPLOADED = "photo-uploaded"
GROUP_ID = "photo-worker-group"


async def run_worker():
    consumer = AIOKafkaConsumer(
        TOPIC_PHOTO_UPLOADED,
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id=GROUP_ID,
        enable_auto_commit=False,
        auto_offset_reset="earliest",
    )

    shutdown_event = asyncio.Event()

    loop = asyncio.get_event_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_event.set)

    while not shutdown_event.is_set():
        try:
            await consumer.start()
            logger.info("Kafka consumer started, waiting for messages")

            try:
                async for msg in consumer:
                    if shutdown_event.is_set():
                        break

                    try:
                        data = json.loads(msg.value)
                        photo_id = data["photo_id"]
                        object_key = data["object_key"]
                    except (json.JSONDecodeError, KeyError) as e:
                        logger.error("Invalid message: %s", e)
                        await consumer.commit()
                        continue

                    try:
                        await process_message(photo_id, object_key, msg)
                        await consumer.commit()
                    except Exception as e:
                        logger.error(
                            "Failed to process %s: %s", photo_id, e, exc_info=True,
                        )
                        await consumer.commit()

            finally:
                await consumer.stop()

        except KafkaConnectionError:
            logger.warning("Kafka not available, reconnecting in 5s...")
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.critical("Unexpected error: %s", e, exc_info=True)
            await asyncio.sleep(5)

    logger.info("Worker stopped")
