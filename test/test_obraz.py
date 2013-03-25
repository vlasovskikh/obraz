import shutil
import os
import unittest
import tempfile
import subprocess

from obraz import obraz


class ObrazTest(unittest.TestCase):
    def setUp(self):
        testdir = os.path.dirname(__file__)
        self.datadir = os.path.join(testdir, 'data')

    def do(self, name):
        src = os.path.join(self.datadir, name, 'src')
        site = os.path.join(self.datadir, name, 'site')
        tempdir = tempfile.mkdtemp()
        try:
            basedir = os.path.join(tempdir, 'basedir')
            shutil.copytree(src, basedir)
            obraz(basedir)
            destdir = os.path.join(basedir, '_site')
            diff = subprocess.Popen(['diff', '-urw', site, destdir],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE)
            stdout, stderr = diff.communicate()
            self.assertEqual(diff.returncode, 0, stdout)
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
