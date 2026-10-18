// Cross-platform setup. Never overwrite an existing private configuration.
import { readFileSync, writeFileSync } from 'node:fs';
import { randomBytes } from 'node:crypto';
const template = readFileSync(new URL('../.env.graphhacks.example', import.meta.url), 'utf8');
const config = template.replace('POSTGRES_PASSWORD=GENERATE_ME', `POSTGRES_PASSWORD=${randomBytes(32).toString('hex')}`)
  .replace('FALKORDB_PASSWORD=GENERATE_ME', `FALKORDB_PASSWORD=${randomBytes(32).toString('hex')}`);
try {
  writeFileSync(new URL('../.env.graphhacks', import.meta.url), config, { flag: 'wx', mode: 0o600 });
  console.log('Created private .env.graphhacks. Live model calls are disabled.');
} catch (error) {
  if (error.code !== 'EEXIST') throw error;
  console.log('Existing .env.graphhacks preserved.');
}
