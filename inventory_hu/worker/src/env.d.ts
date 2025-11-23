declare namespace NodeJS {
  interface ProcessEnv {
    RABBITMQ_URL?: string;
    RABBITMQ_QUEUE?: string;
    RABBITMQ_RESPONSE_QUEUE?: string;

    DB_USER?: string;
    DB_PASSWORD?: string;
    DB_SERVER?: string;
    DB_NAME?: string;
  }
}
