import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'shared/peach-qnap.sh'
MOCK = r'''
import json, os, pathlib, sys
p = pathlib.Path(os.environ['MOCK_HOME'])
s = json.loads((p/'state.json').read_text())
cmd = pathlib.Path(sys.argv[0]).name
a = sys.argv[1:]
with (p/'calls.jsonl').open('a') as f: f.write(json.dumps([cmd]+a)+'\n')
def save(): (p/'state.json').write_text(json.dumps(s))
if cmd == 'getcfg':
    field = a[1]
    default = a[a.index('-d')+1] if '-d' in a else ''
    print({'Install_Path':str(p), 'Enable':s.get('enable','TRUE'),
           'MediaPath':s.get('media',''), 'Port':s.get('port','8900'),
           'BindAddress':'0.0.0.0'}.get(field,default))
elif cmd == 'uname': print('x86_64')
elif cmd in ('setcfg','flock','sleep'): pass
elif cmd == 'docker':
    if a[0]=='info': sys.exit(1 if s.get('offline') else 0)
    if a[:2]==['image','inspect']: sys.exit(0 if s.get('image',True) else 1)
    if a[0]=='pull': sys.exit(1 if s.get('pull_fail') else 0)
    if a[:2]==['container','inspect']:
        if not s.get('container'): sys.exit(1)
        if '--format' in a:
            print(s.get('owner','PeachQNAP') if 'Labels' in a[3] else s.get('health','running healthy'))
    if a[:2]==['volume','inspect']:
        if not s.get('volume'): sys.exit(1)
        if '--format' in a: print(s.get('volume_owner','PeachQNAP'))
    if a[:2]==['volume','create']: s['volume']=True; save()
    if a[0]=='stop': sys.exit(1 if s.get('stop_fail') else 0)
    if a[:2]==['container','rm']: s['container']=False; save()
    if a[0]=='run':
        if s.get('run_fail'): sys.exit(1)
        s['container']=True; save()
'''

class LauncherTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.p = Path(self.tmp.name)
        (self.p/'bin').mkdir()
        for command in ['getcfg','setcfg','docker','uname','flock','sleep']:
            f = self.p/'bin'/command
            f.write_text('#!'+sys.executable+'\n'+MOCK)
            f.chmod(0o755)
        src = SOURCE.read_text().replace('PATH=/bin:', f'PATH={self.p}/bin:/bin:')
        src = src.replace('GETCFG=/sbin/getcfg',f'GETCFG={self.p}/bin/getcfg')
        src = src.replace('SETCFG=/sbin/setcfg',f'SETCFG={self.p}/bin/setcfg')
        (self.p/'launcher').write_text(src)
        (self.p/'image.txt').write_text('example/peach@sha256:test\n')

    def tearDown(self): self.tmp.cleanup()

    def run_case(self, action='start', **state):
        (self.p/'state.json').write_text(json.dumps(state))
        r = subprocess.run(['/bin/sh',str(self.p/'launcher'),action],capture_output=True,text=True,
                           env={**os.environ,'MOCK_HOME':str(self.p)})
        calls = [json.loads(x) for x in (self.p/'calls.jsonl').read_text().splitlines()]
        return r,calls

    def test_start_no_media_no_privilege(self):
        r,c = self.run_case()
        self.assertEqual(r.returncode,0,r.stderr)
        run = next(x for x in c if x[:2]==['docker','run'])
        self.assertNotIn('--privileged',run)
        self.assertTrue(any('target=/data' in x for x in run))
        self.assertFalse(any('target=/media' in x for x in run))

    def test_foreign_container_untouched(self):
        r,c=self.run_case(container=True,owner='other')
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(any(x[1:2] in (['stop'],['run']) for x in c))

    def test_foreign_volume_untouched(self):
        r,c=self.run_case(volume=True,volume_owner='other')
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(any(x[:2]==['docker','run'] for x in c))

    def test_pull_failure_preserves_container(self):
        r,c=self.run_case(container=True,image=False,pull_fail=True)
        self.assertNotEqual(r.returncode,0)
        self.assertNotIn(['docker','stop','--time','75','peach-qnap'],c)

    def test_stop_failure_never_removes(self):
        r,c=self.run_case(container=True,stop_fail=True)
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(any(x[:3]==['docker','container','rm'] for x in c))

    def test_remove_preserves_data(self):
        r,c=self.run_case('remove',container=True,volume=True)
        self.assertEqual(r.returncode,0,r.stderr)
        self.assertIn(['docker','container','rm','peach-qnap'],c)
        self.assertFalse(any(x[:3]==['docker','volume','rm'] for x in c))

    def test_disabled_does_not_start(self):
        r,c=self.run_case(enable='FALSE')
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(any(x[:2]==['docker','run'] for x in c))

    def test_invalid_ports(self):
        for port in ['22','65536','8900;touch /tmp/no','']:
            with self.subTest(port=port):
                r,c=self.run_case(port=port)
                self.assertNotEqual(r.returncode,0)

    def test_missing_media_is_not_created(self):
        r,c=self.run_case(media='/share/missing-peach-test-dir')
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(any(x[:2]==['docker','run'] for x in c))

    def test_unhealthy_is_failure(self):
        r,c=self.run_case(health='running unhealthy')
        self.assertNotEqual(r.returncode,0)

    def test_creation_failure_retains_volume(self):
        r,c=self.run_case(run_fail=True)
        self.assertNotEqual(r.returncode,0)
        self.assertTrue(json.loads((self.p/'state.json').read_text())['volume'])

    def test_offline_does_not_remove(self):
        r,c=self.run_case('remove',offline=True,container=True)
        self.assertNotEqual(r.returncode,0)
        self.assertFalse(any(x[:3]==['docker','container','rm'] for x in c))

if __name__=='__main__': unittest.main(verbosity=2)
