import amqp from 'amqplib';
import { config } from './config';
import { getPool, sql } from './db';
import pino from 'pino';

const logger = pino();
// Evitar dependencias de tipos para TextEncoder en TS sin @types/node
declare const TextEncoder: any;

let conn: any = null;
let ch: any = null;

async function processMessage(msg: any) {
  if (!msg) return;
  try {
    const content = msg.content.toString();
    const payload = JSON.parse(content);
    const { requestId, productoId, cantidad } = payload;

    // Validaciones EXACTAS solicitadas
    if (requestId == null || productoId == null || cantidad == null) {
      const err = { requestId, status: 'error', message: 'Por favor, completa todos los campos obligatorios.' };
      logger.error(err);
      // publicar respuesta de error (solo logging aquí)
      if (ch) ch.ack(msg);
      return;
    }
    if (typeof cantidad !== 'number' || cantidad <= 0) {
      const err = { requestId, status: 'error', message: 'La cantidad debe ser un número positivo.' };
      logger.error(err);
      if (ch) ch.ack(msg);
      return;
    }

    const pool: any = await getPool();
    const transaction = new (pool.Transaction)();
    await transaction.begin();
    try {
      const request = transaction.request();
      // Usar parámetros para evitar inyección y aplicar UPDLOCK
      request.input('id', sql.Int, productoId);
      const selectRes = await request.query('SELECT stock FROM Productos WITH (UPDLOCK, ROWLOCK) WHERE id = @id');
      if (selectRes.recordset.length === 0) {
        await transaction.rollback();
        logger.error({ requestId, message: 'Producto no encontrado.' });
        if (ch) ch.ack(msg);
        return;
      }
      const currentStock = selectRes.recordset[0].stock;
      const newStock = currentStock + cantidad;

      const updReq = transaction.request();
      updReq.input('newStock', sql.Int, newStock);
      updReq.input('id', sql.Int, productoId);
      await updReq.query('UPDATE Productos SET stock = @newStock WHERE id = @id');

      const insReq = transaction.request();
      insReq.input('productoId', sql.Int, productoId);
      insReq.input('cantidad', sql.Int, cantidad);
      insReq.input('accion', sql.VarChar(50), 'reabastecer');
      insReq.input('requestId', sql.VarChar(100), requestId);
      await insReq.query('INSERT INTO InventarioHistorial (producto_id, cantidad, accion, request_id) VALUES (@productoId, @cantidad, @accion, @requestId)');

      await transaction.commit();

      // publicar success
      const success = { requestId, status: 'success', message: 'Existencias actualizadas exitosamente' };
      logger.info(success);
      if (conn) {
        const ch2 = await conn.createChannel();
          await ch2.assertQueue(config.responseQueue, { durable: true });
          ch2.sendToQueue(config.responseQueue, Buffer.from(JSON.stringify(success)), { persistent: true });
        await ch2.close();
      }
      if (ch) ch.ack(msg);
    } catch (e) {
      try { await transaction.rollback(); } catch (_) {}
      logger.error({ err: e, requestId });
      if (ch) ch.ack(msg);
    }
  } catch (err) {
    logger.error(err);
    if (ch) ch.ack(msg);
  }
}

export async function startConsumer() {
  conn = await amqp.connect(config.rabbitUrl);
  ch = await conn.createChannel();
  await ch.assertQueue(config.queue, { durable: true });
  await ch.prefetch(1);
  // Typing the callback as any to avoid implicit any errors
  ch.consume(config.queue, (m: any) => { processMessage(m).catch((err: any) => logger.error(err)); });
  logger.info('Worker: listening on ' + config.queue);
}

export async function stopConsumer() {
  if (ch) await ch.close();
  if (conn) await conn.close();
}
