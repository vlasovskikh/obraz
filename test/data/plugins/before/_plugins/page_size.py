import obraz


def process_size(basedir, destdir, site):
    for page in site['pages']:
        page['size'] = len(page['content'])


obraz.processors.insert(0, process_size)
