import asyncio
import json
import uuid
import os
from aio_pika import connect_robust, Message, DeliveryMode

RABBIT_URL = os.environ.get('RABBITMQ_URL', 'amqp://guest:guest@rabbitmq:5672/')
EXCHANGE = ''
QUEUE = 'inventario.reabastecer'

async def publish_reabastecer(payload: dict):
    connection = await connect_robust(RABBIT_URL)
    channel = await connection.channel()
    message = Message(
        json.dumps(payload).encode('utf-8'),
        content_type='application/json',
        delivery_mode=DeliveryMode.PERSISTENT
    )
    await channel.default_exchange.publish(message, routing_key=QUEUE)
    await connection.close()

def build_payload(producto_id: int, cantidad: int):
    return {
        'requestId': str(uuid.uuid4()),
        'productoId': producto_id,
        'cantidad': cantidad
    }
