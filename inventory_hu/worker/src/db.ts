import sql from 'mssql';
import { config } from './config';

let globalPool: any = null;

export async function getPool() {
  if (globalPool) return globalPool;
  globalPool = await sql.connect({
    user: config.db.user,
    password: config.db.password,
    server: config.db.server,
    database: config.db.database,
    options: config.db.options
  });
  return globalPool;
}

export { sql };
