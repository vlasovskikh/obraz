# -*- coding: utf-8 -*-

# Copyright (c) 2012-2014 Andrey Vlasovskikh
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


"""Static site generator in a single Python file mostly compatible with Jekyll.

Usage:
    obraz (build | serve | new PATH) [options]
    obraz -h|--help

Commands:
    build                   Build your site.
    serve                   Serve your site locally.
    new                     Create a new Obraz site scaffold in PATH.

Options:
    -s --source=DIR         Source directory.
    -d --destination=DIR    Destination directory.
    --force                 Force overwriting the destination directory.
    --safe                  Disable custom plugins.

    -w --watch              Watch for changes and rebuild.
    -D --drafts             Render posts in the _drafts folder.
    -H --host=HOSTNAME      Listen at the given hostname.
    -P --port=PORT          Listen at the given port.
    -b --baseurl=URL        Serve the website from the given base URL.

    -q --quiet              Be quiet.
    -t --trace              Display traceback when an error occurs.
    -v --version            Show version.
    -h --help               Show help message.

For documentation see <http://obraz.pirx.ru/>.
"""


from __future__ import unicode_literals
import sys
import os
import re
import shutil
import errno
from glob import glob
from io import BytesIO
from datetime import datetime
from threading import Thread
from time import sleep
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
from docopt import docopt


__all__ = [
    'file_filter', 'template_filter', 'template_renderer', 'loader',
    'processor', 'generator',
]


PAGE_ENCODING = URL_ENCODING = 'UTF-8'
PY2 = sys.version_info < (3,)
DEFAULT_CONFIG = {
    'source': './',
    'destination': './_site',
    'include': ['.htaccess'],
    'exclude': [],
    'exclude_patterns': [
        r'^[\.#].*',
        r'.*~$',
        r'.*\.s[uvw][a-z]$',  # *.swp files, etc.
    ],
    'full_build_patterns': [
        r'_layouts',
        r'_includes',
    ],
    'host': '0.0.0.0',
    'port': '8000',
    'baseurl': '',
}


_quiet = False
_loaders = []
_processors = []
_file_filters = {}
_template_filters = {}
_render_string = lambda string, context, site: string


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


def template_renderer(f):
    """Set a custom template renderer."""
    global _render_string
    _render_string = f
    return f


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
        raise ValueError("Cannot merge '{0!r}' and '{1!r}'".format(x1, x2))


def all_source_files(source, destination):
    dst_base, dst_name = os.path.split(os.path.realpath(destination))
    for source, dirs, files in os.walk(source):
        if os.path.realpath(source) == dst_base and dst_name in dirs:
            dirs.remove(dst_name)
        for filename in files:
            yield os.path.join(source, filename)


def changed_files(source, destination, config, poll_interval=1):
    times = {}
    while True:
        changed = []
        for path in all_source_files(source, destination):
            rel_path = os.path.relpath(path, source)
            if not is_file_visible(rel_path, config):
                continue
            new = os.stat(path).st_mtime
            old = times.get(path)
            if not old or new > old:
                times[path] = new
                changed.append(path)
        if changed:
            yield changed
        sleep(poll_interval)


def is_file_visible(path, config):
    """Check file name visibility according to site settings."""
    parts = path.split(os.path.sep)
    exclude = config.get('exclude', [])
    exclude_patterns = config.get('exclude_patterns', [])
    if path in config.get('include', []):
        return True
    elif any(re.match(pattern, part)
             for pattern in exclude_patterns
             for part in parts):
        return False
    elif any(path.startswith(s) for s in exclude):
        return False
    else:
        return True


def is_underscored(path):
    parts = path.split(os.path.sep)
    return any(part.startswith('_') for part in parts)


def path2url(path):
    m = re.match(r'(.*)[/\\]index.html?$', path)
    if m:
        path = m.group(1) + os.path.sep
    path = os.path.sep + path
    url = pathname2url(path.encode(URL_ENCODING))
    return url.decode('ASCII') if PY2 else url


def url2path(url):
    if url.endswith('/'):
        url += 'index.html'
    path = url2pathname(url.encode('ASCII') if PY2 else url)
    return (path.decode(URL_ENCODING) if PY2 else path).lstrip(os.path.sep)


def make_dirs(path):
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


def exception(e, trace):
    if trace:
        traceback.print_tb(sys.exc_traceback)
    log('Error: {0}'.format(e))


def log(message):
    sys.stderr.write('{0}\n'.format(message))
    sys.stderr.flush()


def progress(msg, xs):
    if _quiet:
        for x in xs:
            yield x
    else:
        size = len(xs)
        for i, x in enumerate(xs, 1):
            yield x
            s = '{0}: {1}% ({2}/{3})'.format(msg, int(i * 100 / size), i, size)
            sys.stderr.write('\r' + s)
        sys.stderr.write('\n')


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


@template_filter('markdownify')
@file_filter(['.md', '.markdown'])
def markdown_filter(s, config):
    return markdown(s)


@fallback_loader
def load_file(path, config):
    if not is_file_visible(path, config) or is_underscored(path):
        return None
    return {
        'files': [{'url': path2url(path), 'path': path}],
    }


@template_renderer
def jinja2_render_string(string, context, config):
    includes = os.path.join(config['source'], '_includes')
    env = Environment(loader=FileSystemLoader(includes))
    for name, f in _template_filters.items():
        env.filters[name] = lambda s: f(s, config)
    t = env.from_string(string)
    return t.render(**context)


def read_template(path):
    with open(path, 'rb') as fd:
        if fd.read(3) != b'---':
            return None
        lines = []
        while True:
            line = fd.readline()
            if re.match(b'^---\r?\n', line):
                break
            elif line == b'':
                return None
            lines.append(line)
        front_matter = BytesIO(b''.join(lines))
        front_matter.name = path
        page = yaml.load(front_matter)
        if not page:
            page = {}
        content = fd.read().decode(PAGE_ENCODING)
        page['content'] = content
        return page


@loader
def load_page(path, config):
    if not is_file_visible(path, config) or is_underscored(path):
        return None
    name, suffix = os.path.splitext(path)
    if suffix in _file_filters:
        dst = '{0}.html'.format(name)
    else:
        dst = path
    page = read_template(os.path.join(config['source'], path))
    if not page:
        return None
    page.update({'url': path2url(dst), 'path': path})
    return {
        'pages': [page]
    }


def read_post(path, date, title, config):
    page = read_template(os.path.join(config['source'], path))
    if not page:
        return None
    if 'date' in page:
        date = page['date']
    permalink = config.get('permalink', '/{year}/{month}/{day}/{title}.html')
    url_vars = {
        'year': '{0:04}'.format(date.year),
        'month': '{0:02}'.format(date.month),
        'day': '{0:02}'.format(date.day),
        'title': title,
    }
    url = pathname2url(permalink.format(**url_vars))
    page.update({'url': url, 'path': path})
    if 'date' not in page:
        date_str = '{year}-{month}-{day}'.format(**url_vars)
        page['date'] = datetime.strptime(date_str, '%Y-%m-%d')
    page['id'] = '/{year}/{month}/{day}/{title}'.format(**url_vars)
    return {
        'posts': [page],
        'tags': dict((tag, [page]) for tag in page.get('tags', [])),
    }


@loader
def load_post(path, config):
    post_re = re.compile('(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})-'
                         '(?P<title>.+)')
    parts = path.split(os.path.sep)
    if '_posts' not in parts:
        return None
    if not is_file_visible(path, config):
        return None
    name, _ = os.path.splitext(os.path.basename(path))
    m = post_re.match(name)
    if not m:
        return None
    date = datetime.strptime('{year}-{month}-{day}'.format(**m.groupdict()),
                             '%Y-%m-%d')
    return read_post(path, date, m.group('title'), config)


@loader
def load_draft(path, config):
    if not config.get('drafts'):
        return None
    if '_drafts' not in path.split(os.path.sep):
        return None
    if not is_file_visible(path, config):
        return None
    title, _ = os.path.splitext(os.path.basename(path))
    return read_post(path, config['time'], title, config)


def render_layout(content, page, site):
    name = page.get('layout', 'nil')
    if name == 'nil':
        return content
    filename = '{0}.html'.format(name)
    layout_file = os.path.join(site['source'], '_layouts', filename)
    layout = read_template(layout_file)
    if not layout:
        raise Exception("Cannot load template: '{0}'".format(layout_file))
    page_copy = page.copy()
    page_copy.pop('layout', None)
    page_copy.pop('content', None)
    layout.update(page_copy)
    context = {
        'site': site,
        'page': layout,
        'content': content,
    }
    content = _render_string(layout['content'], context, site)
    return render_layout(content, layout, site)


def render_page(page, site):
    context = {
        'site': site,
        'page': page,
    }
    content = page['content']
    if not page.get('raw_content', False):
        content = _render_string(content, context, site)
    f = _file_filters.get(file_suffix(page.get('path', '')))
    if f:
        content = f(content, site)
    page['content'] = content
    return render_layout(content, page, site)


@processor
def process_posts(site):
    """Sort and interlink posts."""
    posts = site.setdefault('posts', [])
    posts.sort(key=lambda p: p['date'], reverse=True)
    n = len(posts)
    for i, post in enumerate(posts):
        if i < n - 1:
            post['next'] = posts[i + 1]
        if i > 0:
            post['previous'] = posts[i - 1]


def generate_page(page, site):
    if not page.get('published', True):
        return
    url = page['url']
    dst = os.path.join(site['destination'], url2path(url))
    make_dirs(os.path.dirname(dst))
    with open(dst, 'wb') as fd:
        fd.truncate()
        try:
            rendered = render_page(page, site)
        except Exception as e:
            msg = "Cannot render '{0}': {1}".format(page.get('path'), e)
            raise Exception(msg)
        fd.write(rendered.encode(PAGE_ENCODING))


@generator
def generate_pages(site):
    """Generate pages with YAML front matter."""
    posts = site.get('posts', [])
    pages = site.get('pages', [])
    for page in progress('Generating pages', posts + pages):
        generate_page(page, site)


@generator
def generate_files(site):
    """Copy static files."""
    for file_dict in site.get('files', []):
        src = os.path.join(site['source'], file_dict['path'])
        dst = os.path.join(site['destination'], url2path(file_dict['url']))
        make_dirs(os.path.dirname(dst))
        shutil.copy(src, dst)


def load_plugins(source):
    plugins = sorted(glob(os.path.join(source, '_plugins', '*.py')))
    n = 0
    for plugin in plugins:
        with open(plugin, 'rb') as fd:
            code = fd.read()
            exec(compile(code, plugin, 'exec'), {})
        n += 1
    if n > 0:
        info('Loaded {0} plugins'.format(n))


def build(config):
    site = load_site(config)
    generate_site(site)


def build_delta(paths, config):
    site = load_site_files(paths, config)
    generate_site(site, clean=False)


def load_site_files(paths, config):
    source = config['source']
    info('Loading source files...')
    site = config.copy()
    n = 0
    for path in paths:
        rel_path = os.path.relpath(path, source)
        for f in _loaders:
            data = f(rel_path, site)
            if data:
                n += 1
                site = merge(site, data)
                break
    info('Loaded {0} files'.format(n))
    return site


def load_site(config):
    paths = all_source_files(config['source'], config['destination'])
    return load_site_files(paths, config)


def generate_site(site, clean=True):
    destination = site['destination']
    marker = os.path.join(destination, '.obraz_destination')
    write_denied = os.path.exists(destination) and not os.path.exists(marker)
    if write_denied and not site.get('force'):
        raise Exception("Use --force to overwrite the contents "
                        "of '{0}' not marked as destination "
                        "directory yet".format(destination))
    make_dirs(destination)
    if clean:
        for name in os.listdir(destination):
            remove(os.path.join(destination, name))
        with open(marker, 'wb'):
            pass
    for f in _processors:
        msg = object_name(f)
        info('{0}...'.format(msg))
        f(site)
    info('Site generated successfully')


def make_server(config):
    host = config['host']
    port = int(config['port'])
    baseurl = config['baseurl']

    class Handler(SimpleHTTPRequestHandler):
        def send_head(self):
            if not self.path.startswith(baseurl):
                self.send_error(404, 'File not found')
                return None
            self.path = self.path[len(baseurl):]
            if not self.path.startswith('/'):
                self.path = '/' + self.path
            return SimpleHTTPRequestHandler.send_head(self)

    return HTTPServer((host, port), Handler)


def serve(config):
    build(config)
    server = make_server(config)
    os.chdir(config['destination'])
    log_serving(config)
    server.serve_forever()


def watch(config):
    source = os.path.abspath(config['source'])
    destination = os.path.abspath(config['destination'])
    initial_dir = os.getcwd()
    serving = False
    server = make_server(config)

    for changed in changed_files(source, destination, config):
        if serving:
            info('Changed {0} files, regenerating...'.format(len(changed)))
            server.shutdown()
            os.chdir(initial_dir)
        try:
            if full_build_required(changed, config) or not serving:
                build(config)
            else:
                build_delta(changed, config)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            exception(e, config.get('trace'))
        os.chdir(destination)
        log_serving(config)
        thread = Thread(target=server.serve_forever)
        thread.daemon = True
        thread.start()
        if not serving:
            serving = True


def log_serving(config):
    url = 'http://{host}:{port}{baseurl}'.format(**config)
    if not url.endswith('/'):
        url += '/'
    info('Serving at {0}'.format(url))


def full_build_required(changed_paths, config):
    patterns = config.get('full_build_patterns', [])
    source = os.path.abspath(config['source'])
    for path in changed_paths:
        parts = os.path.relpath(path, source).split(os.path.sep)
        if any(re.match(pattern, part)
               for pattern in patterns
               for part in parts):
            return True
    return False


def new_site(path):
    from site import USER_BASE

    if os.path.exists(path) and os.listdir(path):
        raise Exception("Path '{0}' exists and is not empty".format(path))
    dev_source = os.path.join(os.path.dirname(__file__), 'scaffold')
    user_source = os.path.join(USER_BASE, 'obraz/scaffold')
    if os.path.exists(dev_source):
        source = dev_source
    elif os.path.exists(user_source):
        source = user_source
    else:
        source = os.path.join(sys.prefix, 'obraz/scaffold')
    shutil.copytree(source, path)
    info("New Obraz site installed in '{0}'".format(path))


def obraz(argv):
    opts = docopt(__doc__, argv=argv, version='0.9')
    global _quiet
    _quiet = opts['--quiet']

    try:
        if opts['new']:
            new_site(opts['PATH'])
            return

        config = DEFAULT_CONFIG.copy()
        source = opts['--source'] if opts['--source'] else './'
        config_file = os.path.join(source, '_config.yml')
        config.update(load_yaml_mapping(config_file))
        config['time'] = datetime.utcnow()
        for k, v in opts.items():
            if k.startswith('--') and v:
                config[k[2:]] = v

        info('Source: {0}'.format(os.path.abspath(config['source'])))
        info('Destination: {0}'.format(os.path.abspath(config['destination'])))

        if not config.get('safe'):
            load_plugins(source)

        if opts['build']:
            build(config)
        elif opts['serve']:
            if opts['--watch']:
                watch(config)
            else:
                serve(config)
    except KeyboardInterrupt:
        info('Interrupted')
    except BaseException as e:
        exception(e, opts['--trace'])
        raise


def main():
    sys.modules['obraz'] = sys.modules[__name__]
    try:
        obraz(sys.argv[1:])
    except Exception:
        sys.exit(1)


if __name__ == '__main__':
    main()
