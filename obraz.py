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

    obraz [-h|--help] /path/to/site

For documentation see <http://obraz.pirx.ru/>."""


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
except ImportError:
    from urllib import pathname2url, url2pathname

import yaml
from markdown import markdown
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateSyntaxError


PAGE_ENCODING = 'UTF-8'

loaders = []
processors = []
file_filters = {
    '.md':          markdown,
    '.markdown':    markdown,
}
template_filters = {
    'markdownify':  markdown,
}
retcode = 0


default_site = {
    'include': ['.htaccess'],
    'exclude_patterns': [
        r'^[\.#_].*',
        r'.*~$',
        r'.*\.s[uvw][a-z]$',  # *.swp files, etc.
    ],
}


def all_files(basedir):
    for path, dirs, files in os.walk(basedir):
        for filename in files:
            yield os.path.join(path, filename)


def load_yaml_mapping(filename):
    try:
        with open(filename, 'rb') as fd:
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


def is_file_visible(filename, site):
    parts = filename.split(os.path.sep)
    exclude = site.get('exclude', [])
    exclude_patterns = site.get('exclude_patterns', [])
    if filename in site.get('include', []):
        return True
    elif any(re.match(pattern, part)
             for pattern in exclude_patterns
             for part in parts):
        return False
    elif any(filename.startswith(path) for path in exclude):
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


def log(message):
    sys.stderr.write('{0}\n'.format(message))
    sys.stderr.flush()


def file_suffix(filename):
    _, ext = os.path.splitext(filename)
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
        global retcode
        retcode = 1
        log('Error when {0}: {1}'.format(message, e))
        log(traceback.format_exc())


def load_file(basedir, filename, site):
    if not is_file_visible(filename, site):
        return None
    return {
        'files': [{'url': path2url(filename), 'source': filename}],
    }


def render_string(basedir, s, context, filename, offset=0):
    includes = os.path.join(basedir, '_includes')
    env = Environment(loader=FileSystemLoader(includes))
    env.filters.update(template_filters)
    try:
        t = env.from_string(s)
        return t.render(**context)
    except TemplateSyntaxError as e:
        raise Exception('{0}:{1}: {2}'.format(filename, e.lineno + offset,
                                              e.message))


def read_template(filename):
    with open(filename, 'rb') as fd:
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


def read_page(basedir, filename, url):
    page = read_template(os.path.join(basedir, filename))
    if not page:
        return None
    page['url'] = url
    f = file_filters.get(file_suffix(filename))
    if f:
        page['content'] = f(page['content'])
    return page


def load_page(basedir, filename, site):
    if not is_file_visible(filename, site):
        return None
    name, suffix = os.path.splitext(filename)
    if suffix in file_filters:
        dst = '{0}.html'.format(name)
    else:
        dst = filename
    page = read_page(basedir, filename, path2url(dst))
    if not page:
        return None
    return {
        'pages': [page]
    }


def load_post(basedir, filename, site):
    post_re = re.compile('(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})-'
                         '(?P<title>.+)')
    parts = filename.split(os.path.sep)
    if '_posts' not in parts:
        return None
    _, name = os.path.split(filename)
    if not is_file_visible(name, site):
        return None
    name, suffix = os.path.splitext(name)
    m = post_re.match(name)
    if not m:
        return None
    permalink = site.get('permalink', '/{year}/{month}/{day}/{title}.html')
    url = pathname2url(permalink.format(**m.groupdict()))
    page = read_page(basedir, filename, url)
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


def render_layout(basedir, content, page, site):
    name = page.get('layout', 'nil')
    if name == 'nil':
        return content
    layout_file = os.path.join(basedir, '_layouts', '{0}.html'.format(name))
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
    content = render_string(basedir, layout['content'], context, layout_file,
                            offset)
    return render_layout(basedir, content, layout, site)


def render_page(basedir, page, site):
    context = {
        'site': site,
        'page': page,
    }
    page_file = url2path(page['url'])
    offset = page.get('_content_offset', 0)
    content = render_string(basedir, page['content'], context, page_file,
                            offset)
    return render_layout(basedir, content, page, site)


def process_posts(basedir, destdir, site):
    """Sort and interlink posts."""
    posts = site.setdefault('posts', [])
    posts.sort(key=lambda post: post['date'], reverse=True)
    n = len(posts)
    for i, post in enumerate(posts):
        if i < n - 1:
            post['next'] = posts[i + 1]
        if i > 0:
            post['previous'] = posts[i - 1]


def generate_pages(basedir, destdir, site):
    """Generate pages with YAML front matter."""
    for page in site.get('pages', []):
        if not page.get('published', True):
            continue
        url = page['url']
        with report_exceptions('generating page {0}'.format(url)):
            dst = os.path.join(destdir, url2path(url))
            makedirs(os.path.dirname(dst))
            with open(dst, 'wb') as fd:
                fd.truncate()
                rendered = render_page(basedir, page, site)
                fd.write(rendered.encode(PAGE_ENCODING))


def generate_files(basedir, destdir, site):
    """Copy static files."""
    for file_dict in site.get('files', []):
        src = os.path.join(basedir, file_dict['source'])
        dst = os.path.join(destdir, url2path(file_dict['url']))
        makedirs(os.path.dirname(dst))
        shutil.copy(src, dst)


def load_plugins(basedir):
    plugins = sorted(glob(os.path.join(basedir, '_plugins', '*.py')))
    n = 0
    for plugin in plugins:
        with report_exceptions('loading {0}'.format(plugin)):
            with open(plugin, 'rb') as fd:
                code = fd.read()
                exec(code, {})
            n += 1
    if n > 0:
        log('Loaded {0} plugins'.format(n))


def load_site(basedir):
    log('Loading source files...')
    site = load_yaml_mapping(os.path.join(basedir, '_config.yml'))
    site = merge(site, default_site)
    site['time'] = datetime.utcnow()
    n = 0
    for i, abspath in enumerate(all_files(basedir)):
        relpath = os.path.relpath(abspath, basedir)
        with report_exceptions('loading {0}'.format(relpath)):
            for loader in loaders:
                data = loader(basedir, relpath, site)
                if data:
                    n += 1
                    site = merge(site, data)
                    break
    log('Loaded {0} files'.format(n))
    return site


def generate_site(basedir, site):
    destdir = os.path.join(basedir, '_site')
    makedirs(destdir)
    for name in os.listdir(destdir):
        remove(os.path.join(destdir, name))
    for processor in processors:
        msg = object_name(processor)
        log('{0}...'.format(msg))
        with report_exceptions(msg):
            processor(basedir, destdir, site)
    if retcode == 0:
        log('Site generated successfully')
    else:
        log('Generation failed, check output for details')


def obraz(basedir):
    load_plugins(basedir)
    site = load_site(basedir)
    generate_site(basedir, site)


def main():
    args = sys.argv[1:]
    if '-h' in args or '--help' in args or not args:
        log(__doc__)
        sys.exit(1)
    obraz(args[0])
    sys.exit(retcode)


loaders.extend([
    load_post,
    load_page,
    load_file,
])


processors.extend([
    process_posts,
    generate_pages,
    generate_files,
])


if __name__ == '__main__':
    sys.modules['obraz'] = sys.modules[__name__]
    main()
