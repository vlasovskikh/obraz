from __future__ import unicode_literals
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

    def do(self, name, extra_args=()):
        src = os.path.join(self.datadir, name, 'src')
        site = os.path.join(self.datadir, name, 'site')
        tempdir = tempfile.mkdtemp()
        try:
            source = os.path.join(tempdir, 'source')
            shutil.copytree(src, source)
            os.chdir(source)
            obraz.obraz(['build', '-q', '-t'] + list(extra_args))
            destination = os.path.join(source, '_site')
            diff = subprocess.Popen(['diff', '-urw', site, destination],
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

    def test_filters_after_rendering(self):
        """Issue #9."""
        self.do('filters_after_rendering')

    def test_custom_template_renderer(self):
        self.do('custom_template_renderer')

    def test_drafts(self):
        self.do('drafts', ['--drafts'])

    def test_no_drafts(self):
        self.do('no_drafts')

    def test_safe(self):
        self.do('safe', ['--safe'])

    def test_raw_content(self):
        self.do('raw_content')
