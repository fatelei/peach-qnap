"""Run only inside a disposable, initialized upstream Peach container."""
import json
from pathlib import Path
import subprocess
import sys
from peach import access, settings_file

program = Path('/check/password.py').read_text()
path = settings_file.load_config().directory('secrets') / 'access.json'
for password in ('integration-first-password', 'integration-second-password'):
    result = subprocess.run([sys.executable, '-c', program], input=json.dumps({
        'password': password, 'confirmation': password,
    }), text=True, capture_output=True, check=True)
    assert password not in result.stdout + result.stderr
    assert access.verify(access.load(path), password)
assert not access.verify(access.load(path), 'integration-first-password')
assert not (path.stat().st_mode & 0o077)
print('Upstream password setup/reset integration passed.')
