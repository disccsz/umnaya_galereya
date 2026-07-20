import asyncio
import logging
from aiokafka import AIOKafkaProducer
from aiokafka.admin import AIOKafkaAdminClient, NewTopic

from aiokafka.errors import KafkaConnectionError

from app.core.config import settings


logger = logging.getLogger(__name__)

TOPIC_PHOTO_UPLOADED = "photo-uploaded"


class KafkaProducer:
    def __init__(self):
        self._producer: AIOKafkaProducer | None = None

    async def startup(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        )
        try:
            await asyncio.wait_for(self._producer.start(), timeout=settings.SERVICE_TIMEOUT)
        except (KafkaConnectionError, asyncio.TimeoutError):
            logger.warning("Kafka not available at startup — continuing without producer")
            self._producer = None
            return

        admin = AIOKafkaAdminClient(bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS)
        await asyncio.wait_for(admin.start(), timeout=settings.SERVICE_TIMEOUT)
        try:
            topics = await asyncio.wait_for(
                admin.list_topics(),
                timeout=settings.SERVICE_TIMEOUT,
            )
            if TOPIC_PHOTO_UPLOADED not in topics:
                logger.info("Creating topic '%s'", TOPIC_PHOTO_UPLOADED)
                await asyncio.wait_for(
                    admin.create_topics([
                        NewTopic(TOPIC_PHOTO_UPLOADED, num_partitions=1, replication_factor=1),
                    ]),
                    timeout=settings.SERVICE_TIMEOUT,
                )
        finally:
            await admin.close()

    async def send(self, topic: str, key: str, value: bytes):
        if not self._producer:
            logger.info("Kafka producer not connected — retrying...")
            await self.startup()
        if not self._producer:
            logger.error("Kafka unavailable, message not sent")
            raise KafkaConnectionError("Kafka unavailable, message not sent")
        try:
            await asyncio.wait_for(
                self._producer.send_and_wait(topic, value=value, key=key),
                timeout=settings.SERVICE_TIMEOUT,
            )
        except asyncio.TimeoutError:
            logger.error("Kafka send timed out after %ss", settings.SERVICE_TIMEOUT)
            raise KafkaConnectionError("Kafka send timed out")

    async def shutdown(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None
