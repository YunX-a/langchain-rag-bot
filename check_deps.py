from pathlib import Path
import importlib.metadata as md
import subprocess
import sys
import re

REQ_PATH = Path(__file__).parent / "requirements.txt"
if not REQ_PATH.exists():
    print(f"requirements.txt not found at {REQ_PATH}")
    sys.exit(2)

pattern = re.compile(r"^\s*([^#\s\[\]]+)(?:\[[^\]]+\])?\s*==\s*([0-9a-zA-Z\.-]+)")

missing = []
mismatch = []
matched = []
skipped = []

with REQ_PATH.open(encoding='utf-8') as f:
    for i, line in enumerate(f, start=1):
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = pattern.match(line)
        if not m:
            skipped.append((i, line))
            continue
        pkg = m.group(1)
        req_ver = m.group(2)
        found = False
        installed_ver = None
        # Try the package name as-is
        try:
            installed_ver = md.version(pkg)
            found = True
        except Exception:
            # Try a couple of sensible fallbacks
            alt_names = []
            if pkg.endswith('-binary'):
                alt_names.append(pkg.replace('-binary', ''))
            # common dash/underscore difference
            if '-' in pkg:
                alt_names.append(pkg.replace('-', '_'))
            if '_' in pkg:
                alt_names.append(pkg.replace('_', '-'))
            for alt in alt_names:
                try:
                    installed_ver = md.version(alt)
                    found = True
                    pkg = alt
                    break
                except Exception:
                    pass
        if not found:
            missing.append((line, req_ver))
        else:
            if installed_ver == req_ver:
                matched.append((pkg, req_ver))
            else:
                mismatch.append((pkg, req_ver, installed_ver))

# Print detailed report
print("Dependency check against requirements.txt:\n")
if matched:
    print(f"OK ({len(matched)}) - matching versions:")
    for pkg, v in matched:
        print(f"  {pkg}=={v}")
    print()

if mismatch:
    print(f"MISMATCH ({len(mismatch)}) - installed version differs:")
    for pkg, req_v, inst_v in mismatch:
        print(f"  {pkg}: required {req_v}  installed {inst_v}")
    print()

if missing:
    print(f"MISSING ({len(missing)}) - not installed:")
    for line, v in missing:
        print(f"  {line}")
    print()

if skipped:
    print(f"SKIPPED ({len(skipped)}) - lines not parsed (maybe editable/git deps or different operators):")
    for ln, text in skipped:
        print(f"  line {ln}: {text}")
    print()

# Run `pip check` to surface dependency conflicts
print("Running `python -m pip check` to detect dependency conflicts...\n")
try:
    res = subprocess.run([sys.executable, '-m', 'pip', 'check'], capture_output=True, text=True, check=False)
    out = res.stdout.strip()
    err = res.stderr.strip()
    if out:
        print("pip check output:\n")
        print(out)
    else:
        print("pip check: no broken requirements reported.")
    if err:
        print('\npip check stderr:')
        print(err)
except Exception as e:
    print(f"Failed to run pip check: {e}")

# Summary
print('\nSummary:')
print(f'  total parsed: {len(matched) + len(mismatch) + len(missing)}')
print(f'  ok: {len(matched)}')
print(f'  mismatches: {len(mismatch)}')
print(f'  missing: {len(missing)}')
print(f'  skipped: {len(skipped)}')

if missing or mismatch:
    print('\nTo install/repair, run:')
    print('  python -m pip install -r requirements.txt')
    sys.exit(1)
else:
    print('\nAll required packages appear installed with matching versions.')
    sys.exit(0)

