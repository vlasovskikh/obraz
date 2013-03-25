import shutil
import imp
import os
import unittest
import tempfile
import subprocess
import sys

import obraz


class ObrazTest(unittest.TestCase):
    def setUp(self):
        imp.reload(obraz)
        testdir = os.path.dirname(__file__)
        self.datadir = os.path.join(testdir, 'data')

    def do(self, name):
        src = os.path.join(self.datadir, name, 'src')
        site = os.path.join(self.datadir, name, 'site')
        tempdir = tempfile.mkdtemp()
        try:
            basedir = os.path.join(tempdir, 'basedir')
            shutil.copytree(src, basedir)
            obraz.obraz(basedir)
            destdir = os.path.join(basedir, '_site')
            diff = subprocess.Popen(['diff', '-urw', site, destdir],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            stdout, stderr = diff.communicate()
            if diff.returncode != 0:
                sys.stderr.write(stdout.decode('UTF-8'))
                self.assertEqual(diff.returncode, 0)
        finally:
            shutil.rmtree(tempdir)

    def test_files(self):
        self.do('files')

    def test_markdown_pages(self):
        self.do('markdown_pages')

    def test_rendered_pages(self):
        self.do('rendered_pages')

    def test_posts(self):
        self.do('posts')

    def test_plugins(self):
        self.do('plugins')
