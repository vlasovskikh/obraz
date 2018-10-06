---
layout: default
title: Obraz Plugins
---

{{ page.title }}
================

Plugins allow extending the site generation process via user-defined processing
functions.

Consider a photo hosting example. By writing a custom plugin you can:

* Use album data from your media library stored in a SQL database
* Add EXIF metadata from images to your photo pages
* Generate re-sized images and thumbnails

Plugins are Python files that should be put into the `_plugins` directory of
the site.

Obraz plugins are incompatible with Jekyll plugins, see
<a href="{{ site.baseurl }}/jekyll.html">compatiblity with Jekyll</a>.


Available Plugins
-----------------

* [Tags](https://github.com/vlasovskikh/obraz/blob/master/doc/_plugins/tags.py)
  by [Andrey Vlasovskikh](http://pirx.ru/): Generate per-tag pages

_Note:_ You can add your plugins to this list by sending a pull request to the
[Obraz repository][3] on GitHub.


Site Model
----------

Internally Obraz represents the site being generated as a Python dictionary.
This is the same dictionary as `site` in Jekyll [template data][2].

The generation process is split into three steps:

1. Loader functions populate the site dictionary by reading files from the
   source directory
2. Processor functions modify the site dictionary (e.g. sort data)
3. Generator functions create files in the destination directory based on the
   site dictionary

Functions for all these steps are registered via extension point decorators.
This applies to third-party plugin functions as well as to the processing
functions in Obraz itself.

There are also a couple of extension points that allow to change define content
and template filters, or change the template system.


Extension Points
----------------

* **`@obraz.loader`**

    Register a site source content loader.

    Source content loaders transform a file path from the site source directory
    into a dictionary that will be merged by Obraz into the `site` dictionary.
    If the loader wants to skip a file and pass it to other loaders, then it
    should return `None`. Loaders are not allowed to modify their `config`
    parameter.

    Loaders are useful when you have source files in some format that you want
    to parse and make available as a part of the site dictionary instead of
    treating them like pages with YAML front matter or regular static files.

    A site content loader is a fuction of type `(path: str, config: dict) ->
    dict`.

    Example:

        import os
        import xml.etree.ElementTree as etree
        import obraz

        @obraz.loader
        def load_checkins(path, config):
            """Loading check-ins from a KML file."""
            if not obraz.is_file_visible(path, config):
                return None
            if not path.endswith('.kml'):
                return None
            root = etree.parse(os.path.join(config['source'], path))
            return {
                'checkins': root.findall('Folder/Placemark'),
            }

* **`@obraz.processor`**

    Register a site content processor.

    Content processors are useful when you need to extend or rearrange already
    existing site data. Site data includes options from the configuration file.

    A site content processor is a fuction of type `(site: dict) -> None`.

    Example:

        import os
        import obraz
        from PIL import Image
        from PIL.ExifTags import TAGS


        def read_exif(path):
            img = Image.open(path)
            exif = img._getexif()
            if exif:
                return {TAGS[k]: v for k, v in exif.items() if k in TAGS}
            else:
                return {}


        @obraz.processor
        def process_exif(site):
            """Processing EXIF metadata."""
            for file in site.get('files', []):
                path = os.path.join(site['source'], file['source'])
                if not path.endswith('.jpg'):
                    continue
                exif = read_exif(path)
                if exif:
                    file['exif'] = exif

* **`@obraz.generator`**

    Register a generator of destination files for the site.

    Generators are useful when you need to create additional generated files
    you need at your site, e.g. tag pages or image thumbnails. Site data
    includes options from the configuration file.

    A site content generator is a fuction of type `(site: dict) -> None`.

        import os
        import obraz
        from PIL import Image

        size = 300

        @obraz.generator
        def generate_thumbnails(site):
            """Generating thumbnails."""
            for file in site.get('files', []):
                path = file['source']
                if not path.endswith('.jpg'):
                    return None
                img = Image.open(os.path.join(site['source'], path))
                img.thumbnail((size, size), Image.ANTIALIAS)
                name, ext = os.path.splitext(path)
                new_path = '{0}-{1}{2}'.format(name, size, ext)
                img.save(os.path.join(site['destination'], new_path), 'JPEG')


* **`@obraz.file_filter(extensions)`**

    Register a page content filter for file extensions.

    File filters are useful for supporting alternative markup languages, such
    as Textile or ReStructured Text.

    A file filter is a function of type `(content: str, config: dict) -> str`.

    Example:

        import obraz
        from markdown import markdown

        @obraz.file_filter(['.md', '.mkdn'])
        def markdown_filter(content, config):
            """Render Mardown files with tables and footnotes extensions."""
            return markdown(content, ['tables', 'footnotes'])

* **`@obraz.template_filter(name)`**

    Register a template filter. Jinja2 [template filters][1] allow filtering
    variables in templates.

    A template filter is a function of type `(content: str, config: dict) ->
    str`.

    Example:

        import obraz
        from markdown import markdown

        @obraz.template_filter('markdownify')
        def markdownify(content, config):
            """Markdown Jinja2 template filter."""
            return markdown(content)

* **`@obraz.template_renderer`**

    Set a custom template renderer. You can change the template system used by
    Obraz.

    A template renderer is a function of type `(string: str, context: dict,
    config: dict) -> str`.

    Example:

        import obraz
        from mako.template import Template
        from mako.lookup import TemplateLookup

        @obraz.template_renderer
        def mako_render_string(string, context, config):
            """Render string using Mako template library."""
            includes = os.path.join(config['source'], '_includes')
            lookup = TemplateLookup(directories=[includes])
            return Template(string, lookup=lookup).render(**context)


Development Notes
-----------------

The easiest way of getting started with plugin development is to read source
code of other plugins.

Please document your plugin carefully in the plugin file docstring. Don't
forget to mention Obraz version compatiblity, required libraries, configuration
parameters.

If a plugin needs configuration parameters, the best place for them is a
separate section in `_config.yml`. The contents of this YAML file will
be available for the plugin as a part of `site`.

You may use all functions defined in `obraz`, but they are not a part of the
plugins API and may be changed or removed in future versions.


  [1]: http://jinja.pocoo.org/docs/templates/#filters
  [2]: http://jekyllrb.com/docs/variables/
  [3]: https://github.com/vlasovskikh/obraz
