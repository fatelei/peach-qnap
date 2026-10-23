import os
from pathlib import Path
import subprocess
import tempfile
import unittest

SOURCE = Path(__file__).resolve().parents[1] / 'shared/peach-admin-link.sh'

class AdminLinkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.link = self.root / 'entry.cgi'
        self.target = self.root / 'peach-admin.cgi'
        self.target.write_text('#!/bin/sh\nexit 0\n')
        self.target.chmod(0o755)
        getter = self.root / 'getcfg'
        getter.write_text('#!/bin/sh\ncase "$2" in Install_Path) echo "'+str(self.root)+'";; *) echo 5000;; esac\n')
        getter.chmod(0o755)
        setter = self.root / 'setcfg'
        setter.write_text('#!/bin/sh\nprintf "%s\\n" "$*" >> "'+str(self.root / 'settings')+'"\n')
        setter.chmod(0o755)
        src = SOURCE.read_text().replace('GETCFG=/sbin/getcfg', 'GETCFG='+str(getter)).replace('SETCFG=/sbin/setcfg', 'SETCFG='+str(setter)).replace('LINK=/home/httpd/cgi-bin/peach-qnap.cgi', 'LINK='+str(self.link))
        self.script = self.root / 'link.sh'
        self.script.write_text(src)

    def run_link(self, action):
        return subprocess.run(['sh',str(self.script),action], capture_output=True, text=True)

    def test_install_reinstall_and_remove(self):
        for _ in range(2):
            result=self.run_link('install')
            self.assertEqual(result.returncode,0,result.stderr)
            self.assertEqual(self.link.readlink(), self.target)
        self.assertIn('Web_Port 5000', (self.root/'settings').read_text())
        self.assertEqual(self.run_link('remove').returncode,0)
        self.assertFalse(self.link.exists())
        self.assertTrue(self.target.exists())

    def test_foreign_link_untouched(self):
        self.link.symlink_to('/other/owner')
        self.assertNotEqual(self.run_link('install').returncode,0)
        self.assertEqual(self.run_link('remove').returncode,0)
        self.assertEqual(str(self.link.readlink()),'/other/owner')

    def test_foreign_file_untouched(self):
        self.link.write_text('owned by another app')
        self.assertNotEqual(self.run_link('install').returncode,0)
        self.run_link('remove')
        self.assertEqual(self.link.read_text(),'owned by another app')
