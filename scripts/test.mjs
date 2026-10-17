import { spawnSync } from 'node:child_process';
import { existsSync } from 'node:fs';
import { resolve, delimiter } from 'node:path';
const windows = process.platform === 'win32';
const python = resolve(windows ? '.venv/Scripts/python.exe' : '.venv/bin/python');
if (!existsSync(python)) throw new Error('Create .venv and install backend/requirements-test.txt first.');
const paths = [resolve('backend')];
if (windows) paths.push(resolve('.venv/Lib/site-packages'));
const env = { ...process.env, PYTHONPATH: paths.join(delimiter),
  DATABASE_URL: process.env.CX_TEST_DATABASE_URL || 'postgresql://test:clearancex_local_test_only@localhost:5449/clearancex_test',
  FALKORDB_PORT: process.env.CX_TEST_GRAPH_PORT || '6399', FALKORDB_PASSWORD: 'clearancex_graph_test_only',
  ENABLE_LIVE_AGENT: 'false', CLEARANCEX_LOCAL_EXTRACTION: 'true' };
const result = spawnSync(python, ['-m', 'pytest', 'backend/tests',
  'backend/reasoning/test_entity_resolution.py', 'backend/reasoning/test_cusdec_readiness.py',
  'backend/reasoning/test_cusdec_xml.py', '-q'], { env, stdio: 'inherit' });
process.exit(result.status ?? 1);
