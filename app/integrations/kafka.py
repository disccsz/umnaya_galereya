import asyncio
import logging
from aiokafka import AIOKafkaProducer

from aiokafka.errors import KafkaConnectionError 

from app.core.config import settings

logger = logging.getLogger(__name__)


class KafkaProducer:
    def __init__(self):
        self._producer: AIOKafkaProducer | None = None

    async def startup(self):
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            sasl_mechanism="PLAIN",
            sasl_plain_username=settings.KAFKA_SASL_USERNAME,
            sasl_plain_password=settings.KAFKA_SASL_PASSWORD,
        )
        try:
            await asyncio.wait_for(self._producer.start(), timeout=settings.SERVICE_TIMEOUT)
        except (KafkaConnectionError, asyncio.TimeoutError):
            logger.warning("Kafka not available at startup — continuing without producer")
            await self._producer.stop()
            self._producer = None

    async def send(self, topic: str, key: bytes, value: bytes):
        if not self._producer:
            logger.warning("Kafka producer not connected, message dropped")
            return
        await self._producer.send_and_wait(topic, value=value, key=key)

    async def shutdown(self):
        if self._producer:
            await self._producer.stop()
            self._producer = None

