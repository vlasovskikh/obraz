---
layout: default
title: Obraz Plugin System
---

{{ page.title }}
================

TODO: Document the Obraz plugins API, available bundled and third-party
plugins.

TODO: Describe what is the site for Obraz. Describe the load, process and
generate stages of site processing.


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

    Register a template filter.

    A template filter is a function of type `(content: str) -> str`.

    TODO

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
