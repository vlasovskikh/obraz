---
layout: default
title: Obraz Plugin System
---

{{ page.title }}
================

_The Obraz plugin system is still considered experimental and may be changed
significantly in the future versions._


Site Model
----------

Obraz represents the site being generated as a Python dictionary internally. It
is the same dictionary as `site` in Jekyll [template data][2].

The generation process consists of three steps:

1. Loader functions populate the site dictionary by reading source files from
   the base directory
2. Processor functions modify the site dictionary (e.g. sort data)
3. Generator functions create files in the destination directory based on the
   site dictionary

Functions for all these steps are registered via extension point decorators.
This applies to third-party plugin functions as well as to the processing
functions in Obraz itself.

There are also a couple of extension points that allow to define content and
template filters.


Plugins
-------

Plugins are Python files that should be put into the `_plugins` directory of
the site. Plugins can import the `obraz` module and register extension
functions via extension point decorators.

_Note:_ There will be a third-party plugin repository with commonly used
plugins.


Extension Points
----------------

* **`@obraz.file_filter(extensions)`**

    Register a page content filter for file extensions.

    File filters are useful for supporting alternative markup languages, such
    as Textile or ReStructured Text.

    A file filter is a function of type `(content: str) -> str`.

    Example:

        import obraz
        from markdown import markdown

        @obraz.file_filter(['.md', '.mkdn'])
        def markdown_filter(content):
            return markdown(content, ['tables', 'footnotes'])

* **`@obraz.template_filter(name)`**

    Register a template filter. Jinja2 [template filters][1] allow filtering
    variables in templates.

    A template filter is a function of type `(content: str) -> str`.

    Example:

        import obraz
        from markdown import markdown

        @obraz.template_filter('markdownify')
        def markdownify(content):
            return markdown(content)

* **`@obraz.loader`**

    Register a site source content loader.

    A site content loader is a fuction of type `(basedir: str, filename: str,
    site: dict) -> dict`.

    TODO

* **`@obraz.processor`**

    Register a site content processor.

    A site content processor is a fuction of type `(basedir: str, destdir: str,
    site: dict) -> None`.

    TODO

* **`@obraz.generator`**

    Register a generator of destination files for the site.

    A site content generator is a fuction of type `(basedir: str, destdir: str,
    site: dict) -> None`.

    TODO


Other Functions
---------------

You may use all functions defined in `obraz`, but they are not a part of the
plugins API and may be changed or removed in future versions.


  [1]: http://jinja.pocoo.org/docs/templates/#filters
  [2]: http://jekyllrb.com/docs/variables/
