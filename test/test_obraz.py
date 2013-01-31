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
        before = os.path.join(self.datadir, name, 'before')
        after = os.path.join(self.datadir, name, 'after')
        tempdir = tempfile.mkdtemp()
        try:
            basedir = os.path.join(tempdir, 'basedir')
            shutil.copytree(before, basedir)
            obraz(basedir)
            diff = subprocess.Popen(['diff', '-urw', after, basedir],
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
