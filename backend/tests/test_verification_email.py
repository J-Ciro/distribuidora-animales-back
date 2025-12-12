import sys
import os

# Añadir el directorio padre al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import pika
import json

# Configuración de RabbitMQ
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'

async def send_verification_email_test():
    """Enviar un mensaje de prueba a la cola de emails para verificar la configuración"""
    
    # Conectar a RabbitMQ
    credentials = pika.PlainCredentials(RABBITMQ_USER, RABBITMQ_PASSWORD)
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            credentials=credentials
        )
    )
    channel = connection.channel()
    
    # Mensaje de prueba para verificación de email
    test_message = {
        "to": "paulagutierrez0872@gmail.com",  # Email de prueba
        "subject": "Código de Verificación - Distribuidora Perros y Gatos",
        "template": "verification",
        "context": {
            "username": "Usuario Prueba",
            "verificationCode": "123456"
        }
    }
    
    # Enviar mensaje a la cola
    channel.queue_declare(queue='email.notifications', durable=True)
    channel.basic_publish(
        exchange='',
        routing_key='email.notifications',
        body=json.dumps(test_message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # Hacer el mensaje persistente
            content_type='application/json'
        )
    )
    
    print("✅ Mensaje de prueba enviado a la cola 'email.notifications'")
    print(f"📧 Destinatario: {test_message['to']}")
    print(f"📝 Asunto: {test_message['subject']}")
    print("\n⏳ Revisa los logs del worker para confirmar el envío:")
    print("   docker-compose logs -f worker")
    print("\n📨 El email debe enviarse desde: distribuidoraperrosgatos@gmail.com")
    print("\n🔍 Revisa la bandeja de entrada de:", test_message['to'])
    
    connection.close()

if __name__ == "__main__":
    try:
        asyncio.run(send_verification_email_test())
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
