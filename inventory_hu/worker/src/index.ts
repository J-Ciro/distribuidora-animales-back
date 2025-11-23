import { startConsumer } from './consumer';

(async () => {
  try {
    await startConsumer();
    console.log('Worker started');
  } catch (err) {
    console.error('Worker failed to start', err);
    process.exit(1);
  }
})();
