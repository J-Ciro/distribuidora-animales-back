import dotenv from 'dotenv';
import path from 'path';

dotenv.config({ path: path.resolve(__dirname, '../../.env') });

// Build RabbitMQ URL from environment variables if explicit RABBITMQ_URL is not provided
const rabbitUser = process.env.RABBITMQ_USER || process.env.RABBITMQ_USERNAME || 'guest';
const rabbitPass = process.env.RABBITMQ_PASSWORD || process.env.RABBITMQ_PASS || 'guest';
const rabbitHost = process.env.RABBITMQ_HOST || 'localhost';
const rabbitPort = process.env.RABBITMQ_PORT || '5672';

const defaultRabbitUrl = `amqp://${rabbitUser}:${rabbitPass}@${rabbitHost}:${rabbitPort}/`;

export const config = {
  nodeEnv: process.env.NODE_ENV || 'development',  // Añadido nodeEnv
  rabbitMQ: {
    url: process.env.RABBITMQ_URL || defaultRabbitUrl,
    queues: {
      emailNotifications: 'email.notifications',
      sendEmail: 'send_email_queue',  // Mantenido para compatibilidad
      processOrder: 'process_order_queue',
      updateInventory: 'update_inventory_queue',
      userRegistration: 'user_registration_queue',
      // HU_MANAGE_CATEGORIES queues - EXACT as per specification
      crearCategoria: 'categorias.crear',
      actualizarCategoria: 'categorias.actualizar',
      eliminarCategoria: 'categorias.eliminar',
      crearSubcategoria: 'subcategorias.crear',
      actualizarSubcategoria: 'subcategorias.actualizar',
      eliminarSubcategoria: 'subcategorias.eliminar',
      productosCrear: process.env.RABBITMQ_QUEUE_PRODUCTOS_CREAR || 'productos.crear',
    },
  },
  smtp: {
    host: process.env.SMTP_HOST || 'smtp.gmail.com',
    port: parseInt(process.env.SMTP_PORT || '587', 10),
    user: process.env.SMTP_USER || '',
    pass: process.env.SMTP_PASS || process.env.SMTP_PASSWORD || '',
    from: `${process.env.EMAIL_FROM_NAME || 'Distribuidora Perro y Gatos'} <${process.env.EMAIL_FROM_ADDRESS || process.env.SMTP_USER || 'distribuidoraperrosgatos@gmail.com'}>`
  },
};