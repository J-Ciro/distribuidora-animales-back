import { Channel, ConsumeMessage } from 'amqplib';
import { sendEmail } from '../services/email.service';
import logger from '../utils/logger';
import path from 'path';
import fs from 'fs';
import handlebars from 'handlebars';

// Cargar plantilla
const loadTemplate = (templateName: string): string => {
  try {
    const templatePath = path.join(__dirname, `../../templates/emails/${templateName}.hbs`);
    return fs.readFileSync(templatePath, 'utf8');
  } catch (error) {
    logger.error(`Error cargando la plantilla ${templateName}:`, error);
    throw new Error(`Plantilla ${templateName} no encontrada`);
  }
};

export const consumePasswordResetMessages = async (channel: Channel) => {
  const queue = 'email.password_reset';
  await channel.assertQueue(queue, { durable: true });

  logger.info(`[Password Reset Consumer] Esperando mensajes en ${queue}`);
  
  channel.consume(
    queue,
    async (msg: ConsumeMessage | null) => {
      if (!msg) return;

      try {
        const message = JSON.parse(msg.content.toString());
        logger.info(`[Password Reset Consumer] Procesando mensaje: ${message.requestId}`);

        // Obtener el año actual para el template
        const currentYear = new Date().getFullYear();

        // Cargar la plantilla de recuperación de contraseña
        const templateSource = loadTemplate('password-reset');
        const template = handlebars.compile(templateSource);
        
        // Compilar el HTML con los datos del mensaje
        const html = template({
          resetLink: message.reset_link,
          year: currentYear,
        });

        // Enviar el correo
        await sendEmail({
          to: message.to,
          subject: 'Recupera tu contraseña - Distribuidora Perros y Gatos',
          html,
        });

        // Confirmar el procesamiento
        channel.ack(msg);
        logger.info(`[Password Reset Consumer] Correo de recuperación enviado exitosamente a: ${message.to}`);
        
      } catch (error) {
        logger.error('[Password Reset Consumer] Error procesando mensaje:', error);
        
        // Reintentar más tarde si aún no se ha reintentado
        if (msg.fields.redelivered) {
          // Si ya se reintentó, descartar el mensaje
          channel.ack(msg);
          logger.warn('[Password Reset Consumer] Mensaje descartado después de reintento');
        } else {
          // Reintentar: devolver el mensaje a la queue
          channel.nack(msg, false, true);
          logger.warn('[Password Reset Consumer] Reintentando envío de correo...');
        }
      }
    },
    { noAck: false }
  );
};
