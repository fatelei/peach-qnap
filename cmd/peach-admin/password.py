# MIT. Invoked inside the existing Peach container; input is never an argv value.
import json
import sys
from filelock import FileLock
from peach import access, settings_file

body = json.load(sys.stdin)
password = body['password']
access.validate_password(password, body['confirmation'])
if not password:
    raise ValueError('A password is required')
config = settings_file.load_config()
if not config.present:
    raise ValueError('Peach has not initialized')
path = config.directory('secrets') / 'access.json'
with FileLock(str(path.with_suffix('.lock')), timeout=5):
    access.save(path, password)
print('ok')
