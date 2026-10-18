"""Create a local review archive from an explicit source allowlist, never secrets."""
from pathlib import Path
import argparse
import hashlib
import re
import zipfile

root = Path(__file__).resolve().parents[1]
folders = ['.github/workflows', 'backend/context_app', 'backend/database', 'backend/migrations', 'backend/reasoning', 'backend/ai_pipeline',
    'backend/evaluation', 'backend/tests', 'backend/api', 'frontend/src', 'frontend/public', 'frontend/tests', 'scripts']
names = ['README.md', 'GRAPH_HACKS_WORKPLAN.md', 'compose.yaml', '.env.graphhacks.example', '.gitignore',
    'package.json', 'package-lock.json', 'backend/main.py', 'backend/xai_types.py', 'backend/Dockerfile', 'backend/.dockerignore',
    'backend/requirements.txt', 'backend/requirements-core.txt', 'backend/requirements-ocr.txt', 'backend/requirements-mcp.txt', 'backend/requirements-test.txt',
    'frontend/package.json', 'frontend/package-lock.json', 'frontend/index.html', 'frontend/Dockerfile', 'frontend/.dockerignore', 'frontend/nginx.conf',
    'frontend/vite.config.ts', 'frontend/vitest.config.ts', 'frontend/tsconfig.json', 'frontend/tsconfig.app.json', 'frontend/tsconfig.node.json', 'frontend/.oxlintrc.json']
names += [str(p.relative_to(root)).replace('\\', '/') for p in (root / 'Docs').glob('GRAPH*.md')]
names += [f'Docs/{name}.md' for name in ['LOCAL_SETUP', 'DEMO', 'EVALUATION', 'SUBMISSION_CHECKLIST', 'TEAM_TECHNICAL_BRIEF', 'NINE_FIXES_VERIFICATION', 'LOCAL_RUNTIME_BUG_REPORT', 'FOUR_PDF_VERIFICATION_REPORT']]
names += ['Docs/LEGACY_ROOT_README.md', 'Docs/UI_VERIFICATION_REPORT.md', 'Docs/COMPETITION_AND_SECURITY_REVIEW.md', 'Docs/ADMIN_CUSTOMER_FLOW.md', 'Docs/WEB_POLISH_REPORT.md']
names += [f'Docs/{name}.md' for name in ['COMPETITION_READINESS_REVIEW', 'JUDGE_GUIDE', 'SUBMISSION', 'RELEASE_READINESS', 'MANUAL_ACCEPTANCE', 'ACCEPTANCE_EVALUATION']]
names += [str(p.relative_to(root)).replace('\\', '/') for p in (root / 'output/verification').glob('*.json')]
files = {root / name for name in names if (root / name).is_file()}
for folder in folders:
    files.update(p for p in (root / folder).rglob('*') if p.is_file() and not any(part in {'__pycache__', '.pytest_cache', '.test_uploads', 'node_modules', 'venv'} for part in p.parts)
        and not p.name.startswith('.env') and p.suffix not in {'.pyc', '.pdf', '.png', '.jpg', '.jsonl'}
        and not (folder.startswith('backend/') and p.suffix == '.json'))
required = ['backend/context_app/companies.py', 'frontend/src/components/screens/ScreenAdminDashboard.tsx',
    'frontend/tests/customer-administration.test.tsx', 'backend/evaluation/acceptance_cases.py', '.github/workflows/verify.yml', 'Docs/JUDGE_GUIDE.md']
for name in required:
    if root / name not in files:
        raise SystemExit(f'Required competition source missing: {name}')
for path in files:
    relative = path.relative_to(root)
    if any(part in {'private', 'uploads', 'data', 'sample_docs'} for part in relative.parts):
        raise SystemExit(f'Private data path refused: {relative}')
    if re.search(rb'sk-(?:proj-)?[A-Za-z0-9_-]{30,}', path.read_bytes()):
        raise SystemExit(f'Possible credential found in selected source: {relative}')
destination = root / 'output/release/ClearanceX_Graph_Hacks_Source.zip'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--prepare-checkout', help='Extract a verified clean source tree into this NEW folder; never overwrites files')
parser.add_argument('--write-pathspec', help='Write the exact reviewed source list for scoped Git staging')
args = parser.parse_args()
destination.parent.mkdir(parents=True, exist_ok=True)
manifest = []
with zipfile.ZipFile(destination, 'w', zipfile.ZIP_DEFLATED) as archive:
    for path in sorted(files):
        relative = path.relative_to(root).as_posix()
        archive.write(path, relative)
        manifest.append(f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {relative}')
    archive.writestr('SOURCE_MANIFEST.txt', '\n'.join(manifest) + '\n')
with zipfile.ZipFile(destination) as archive:
    for entry in manifest:
        expected, name = entry.split('  ', 1)
        if hashlib.sha256(archive.read(name)).hexdigest() != expected:
            raise SystemExit(f'Archive hash mismatch: {name}')
if args.write_pathspec:
    Path(args.write_pathspec).write_text('\n'.join(sorted(path.relative_to(root).as_posix() for path in files)) + '\n', encoding='utf-8')
if args.prepare_checkout:
    checkout = Path(args.prepare_checkout).resolve()
    # Restrict generated checkouts to the known private release directory.
    if root / 'output' / 'release' not in checkout.parents:
        raise SystemExit('Clean review checkout must be a NEW folder inside output/release.')
    checkout.mkdir(parents=False, exist_ok=False)
    with zipfile.ZipFile(destination) as archive:
        for name in archive.namelist():
            if not (checkout / name).resolve().is_relative_to(checkout):
                raise SystemExit('Unsafe archive path refused.')
        archive.extractall(checkout)
    print(f'Verified clean review checkout: {checkout.name}')
print(f'Prepared local source review archive: {destination.name}, {len(files)} files. No publishing or event submission performed.')
