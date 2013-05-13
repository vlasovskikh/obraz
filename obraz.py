# -*- coding: utf-8 -*-

# Copyright (c) 2012-2013 Andrey Vlasovskikh
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Static site generator in a single Python file similar to Jekyll.

Usage:
    obraz (build|serve) [options]
    obraz -h|--help

Commands:
    build                   Build your site.
    serve                   Serve your site locally.

Options:
    -s --source=DIR         Source directory.
    -d --destination=DIR    Destination directory.

    --host=HOSTNAME         Listen at the given hostname.
    --port=PORT             Listen at the given port.
    --baseurl=URL           Serve the website from the given base URL.

    -q --quiet              Be quiet.
    -v --version            Show version.
    -h --help               Show help message.

For documentation see <http://obraz.pirx.ru/>."""

from __future__ import unicode_literals
import sys
import os
import re
import shutil
import errno
from glob import glob
from datetime import datetime
from contextlib import contextmanager
import traceback

try:
    from urllib.request import pathname2url, url2pathname
    from http.server import SimpleHTTPRequestHandler, HTTPServer
except ImportError:
    from urllib import pathname2url, url2pathname
    from SimpleHTTPServer import SimpleHTTPRequestHandler
    from BaseHTTPServer import HTTPServer

import yaml
from markdown import markdown
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateSyntaxError
from docopt import docopt


PAGE_ENCODING = 'UTF-8'

_return_code = 0
_quiet = False
_loaders = []
_processors = []
_file_filters = {}
_template_filters = {}
_default_site = {
    'source': './',
    'destination': './_site',
    'include': ['.htaccess'],
    'exclude': [],
    'exclude_patterns': [
        r'^[\.#_].*',
        r'.*~$',
        r'.*\.s[uvw][a-z]$',  # *.swp files, etc.
    ],
    'host': '0.0.0.0',
    'port': '8000',
    'baseurl': '',
}


def file_filter(extensions):
    """Register a page content filter for file extensions."""
    def wrapper(f):
        for ext in extensions:
            _file_filters[ext] = f
        return f
    return wrapper


def template_filter(name):
    """Register a template filter."""
    def wrapper(f):
        _template_filters[name] = f
        return f
    return wrapper


def loader(f):
    """Register a site source content loader."""
    _loaders.insert(0, f)
    return f


def processor(f):
    """Register a site content processor."""
    _processors.insert(0, f)
    return f


def generator(f):
    """Register a destination files generator for the site."""
    _processors.append(f)
    return f


def fallback_loader(f):
    _loaders.append(f)
    return f


def all_files(path):
    for path, dirs, files in os.walk(path):
        for filename in files:
            yield os.path.join(path, filename)


def load_yaml_mapping(path):
    try:
        with open(path, 'rb') as fd:
            mapping = yaml.load(fd)
            return mapping if mapping else {}
    except IOError as e:
        if e.errno == errno.ENOENT:
            return {}


def merge(x1, x2):
    if isinstance(x1, dict) and isinstance(x2, dict):
        res = x1.copy()
        for k, v in x2.items():
            if k in res:
                res[k] = merge(res[k], v)
            else:
                res[k] = v
        return res
    elif isinstance(x1, list) and isinstance(x2, list):
        res = list(x1)
        res.extend(x2)
        return res
    elif x1 == x2:
        return x1
    else:
        raise ValueError("cannot merge '{0!r}' and '{1!r}'".format(x1, x2))


def is_file_visible(path, site):
    """Check file name visibility according to site settings."""
    parts = path.split(os.path.sep)
    exclude = site.get('exclude', [])
    exclude_patterns = site.get('exclude_patterns', [])
    if path in site.get('include', []):
        return True
    elif any(re.match(pattern, part)
             for pattern in exclude_patterns
             for part in parts):
        return False
    elif any(path.startswith(s) for s in exclude):
        return False
    else:
        return True


def path2url(path):
    m = re.match(r'(.*)[/\\]index.html?$', path)
    if m:
        path = m.group(1) + os.path.sep
    return pathname2url(os.path.sep + path)


def url2path(url):
    if url.endswith('/'):
        url += 'index.html'
    return url2pathname(url).lstrip(os.path.sep)


def makedirs(path):
    try:
        os.makedirs(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass


def remove(path):
    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except OSError as e:
        if e.errno == errno.EEXIST:
            pass


def info(message):
    if not _quiet:
        log(message)


def error(message):
    log(message)


def log(message):
    sys.stderr.write('{0}\n'.format(message))
    sys.stderr.flush()


def file_suffix(path):
    _, ext = os.path.splitext(path)
    return ext


def object_name(f):
    if f.__doc__:
        lines = f.__doc__.splitlines()
        for line in lines:
            line = line.strip()
            if line:
                return line.rstrip('.')
    return f.__name__


@contextmanager
def report_exceptions(message):
    try:
        yield
    except Exception as e:
        global _return_code
        _return_code = 1
        error('Error when {0}: {1}'.format(message, e))
        error(traceback.format_exc())


@template_filter('markdownify')
@file_filter(['.md', '.markdown'])
def markdown_filter(s):
    return markdown(s)


@fallback_loader
def load_file(path, site):
    if not is_file_visible(path, site):
        return None
    return {
        'files': [{'url': path2url(path), 'source': path}],
    }


def render_string(source, s, context, path, offset=0):
    includes = os.path.join(source, '_includes')
    env = Environment(loader=FileSystemLoader(includes))
    env.filters.update(_template_filters)
    try:
        t = env.from_string(s)
        return t.render(**context)
    except TemplateSyntaxError as e:
        raise Exception('{0}:{1}: {2}'.format(path, e.lineno + offset,
                                              e.message))


def read_template(path):
    with open(path, 'rb') as fd:
        if fd.read(3) != b'---':
            return None
        lines = []
        offset = 1
        while True:
            line = fd.readline()
            if re.match(b'^---\r?\n', line):
                break
            elif line == b'':
                return None
            lines.append(line)
            offset += 1
        front_matter = b''.join(lines)
        page = yaml.load(front_matter)
        if not page:
            page = {}
        content = fd.read().decode(PAGE_ENCODING)
        page['content'] = content
        page['_content_offset'] = offset
        return page


def read_page(path, url):
    page = read_template(path)
    if not page:
        return None
    page['url'] = url
    f = _file_filters.get(file_suffix(path))
    if f:
        page['content'] = f(page['content'])
    return page


@loader
def load_page(path, site):
    if not is_file_visible(path, site):
        return None
    name, suffix = os.path.splitext(path)
    if suffix in _file_filters:
        dst = '{0}.html'.format(name)
    else:
        dst = path
    page = read_page(os.path.join(site['source'], path), path2url(dst))
    if not page:
        return None
    return {
        'pages': [page]
    }


@loader
def load_post(path, site):
    post_re = re.compile('(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})-'
                         '(?P<title>.+)')
    parts = path.split(os.path.sep)
    if '_posts' not in parts:
        return None
    _, name = os.path.split(path)
    if not is_file_visible(name, site):
        return None
    name, suffix = os.path.splitext(name)
    m = post_re.match(name)
    if not m:
        return None
    permalink = site.get('permalink', '/{year}/{month}/{day}/{title}.html')
    url = pathname2url(permalink.format(**m.groupdict()))
    page = read_page(os.path.join(site['source'], path), url)
    if not page:
        return None
    date_str = '{year}-{month}-{day}'.format(**m.groupdict())
    page.setdefault('date', datetime.strptime(date_str, '%Y-%m-%d'))
    page['id'] = '/{year}/{month}/{day}/{title}'.format(**m.groupdict())
    return {
        'pages': [page],
        'posts': [page],
        'tags': dict((tag, [page]) for tag in page.get('tags', [])),
    }


def render_layout(source, content, page, site):
    name = page.get('layout', 'nil')
    if name == 'nil':
        return content
    layout_file = os.path.join(source, '_layouts', '{0}.html'.format(name))
    layout = read_template(layout_file)
    if not layout:
        raise Exception("cannot load template: '{0}'".format(layout_file))
    page_copy = page.copy()
    page_copy.pop('layout', None)
    page_copy.pop('content', None)
    page_copy.pop('_content_offset', None)
    layout.update(page_copy)
    context = {
        'site': site,
        'page': layout,
        'content': content,
    }
    offset = layout.get('_content_offset', 0)
    content = render_string(source, layout['content'], context, layout_file,
                            offset)
    return render_layout(source, content, layout, site)


def render_page(source, page, site):
    context = {
        'site': site,
        'page': page,
    }
    page_file = url2path(page['url'])
    offset = page.get('_content_offset', 0)
    content = render_string(source, page['content'], context, page_file,
                            offset)
    return render_layout(source, content, page, site)


@processor
def process_posts(site):
    """Sort and interlink posts."""
    posts = site.setdefault('posts', [])
    posts.sort(key=lambda post: post['date'], reverse=True)
    n = len(posts)
    for i, post in enumerate(posts):
        if i < n - 1:
            post['next'] = posts[i + 1]
        if i > 0:
            post['previous'] = posts[i - 1]


@generator
def generate_pages(site):
    """Generate pages with YAML front matter."""
    for page in site.get('pages', []):
        if not page.get('published', True):
            continue
        url = page['url']
        with report_exceptions('generating page {0}'.format(url)):
            dst = os.path.join(site['destination'], url2path(url))
            makedirs(os.path.dirname(dst))
            with open(dst, 'wb') as fd:
                fd.truncate()
                rendered = render_page(site['source'], page, site)
                fd.write(rendered.encode(PAGE_ENCODING))


@generator
def generate_files(site):
    """Copy static files."""
    for file_dict in site.get('files', []):
        src = os.path.join(site['source'], file_dict['source'])
        dst = os.path.join(site['destination'], url2path(file_dict['url']))
        makedirs(os.path.dirname(dst))
        shutil.copy(src, dst)


def load_plugins(source):
    plugins = sorted(glob(os.path.join(source, '_plugins', '*.py')))
    n = 0
    for plugin in plugins:
        with report_exceptions('loading {0}'.format(plugin)):
            with open(plugin, 'rb') as fd:
                code = fd.read()
                exec(code, {})
            n += 1
    if n > 0:
        info('Loaded {0} plugins'.format(n))


def load_site(site):
    source = site['source']
    info('Loading source files...')
    n = 0
    for i, path in enumerate(all_files(source)):
        relpath = os.path.relpath(path, source)
        with report_exceptions('loading {0}'.format(relpath)):
            for loader in _loaders:
                data = loader(relpath, site)
                if data:
                    n += 1
                    site = merge(site, data)
                    break
    info('Loaded {0} files'.format(n))
    return site


def generate_site(site):
    destination = site['destination']
    makedirs(destination)
    for name in os.listdir(destination):
        remove(os.path.join(destination, name))
    for processor in _processors:
        msg = object_name(processor)
        info('{0}...'.format(msg))
        with report_exceptions(msg):
            processor(site)
    if _return_code == 0:
        info('Site generated successfully')
    else:
        info('Generation failed, check output for details')


def build(site):
    info('Source: {0}'.format(os.path.abspath(site['source'])))
    info('Destination: {0}'.format(os.path.abspath(site['destination'])))
    load_plugins(site['source'])
    site = load_site(site)
    generate_site(site)


def serve(site):
    build(site)
    if _return_code > 0:
        sys.exit(_return_code)

    host = site['host']
    port = int(site['port'])
    baseurl = site['baseurl']

    class Handler(SimpleHTTPRequestHandler):
        def send_head(self):
            if not self.path.startswith(baseurl):
                self.send_error(404, 'File not found')
                return None
            self.path = self.path[len(baseurl):]
            if not self.path.startswith('/'):
                self.path = '/' + self.path
            return SimpleHTTPRequestHandler.send_head(self)

    httpd = HTTPServer((host, port), Handler)
    info('Serving at {0}:{1}'.format(host, port))
    os.chdir(site['destination'])
    httpd.serve_forever()


def obraz(argv):
    opts = docopt(__doc__, argv=argv, version='0.3')
    global _quiet
    _quiet = opts['--quiet']

    site = _default_site.copy()
    source = opts['--source'] if opts['--source'] else './'
    config = os.path.join(source, '_config.yml')
    site.update(load_yaml_mapping(config))
    site['time'] = datetime.utcnow()
    for k, v in opts.items():
        if k.startswith('--') and v:
            site[k[2:]] = v

    if opts['build']:
        build(site)
    elif opts['serve']:
        serve(site)


if __name__ == '__main__':
    sys.modules['obraz'] = sys.modules[__name__]
    try:
        obraz(sys.argv[1:])
    except KeyboardInterrupt:
        info('Interrupted')
    sys.exit(_return_code)
