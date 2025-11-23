import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

export const config = {
  rabbitUrl: process.env.RABBITMQ_URL || 'amqp://guest:guest@rabbitmq:5672',
  queue: process.env.RABBITMQ_QUEUE || 'inventario.reabastecer',
  responseQueue: process.env.RABBITMQ_RESPONSE_QUEUE || 'inventario.reabastecer.responses',
  db: {
    user: process.env.DB_USER || 'sa',
    password: process.env.DB_PASSWORD || 'yourStrongPassword123#',
    server: process.env.DB_SERVER || 'sqlserver',
    database: process.env.DB_NAME || 'distribuidora_db',
    options: {
      encrypt: false,
      trustServerCertificate: true
    }
  }
};
