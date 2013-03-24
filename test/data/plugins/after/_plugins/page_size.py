import obraz


@obraz.processor
def process_size(basedir, destdir, site):
    for page in site['pages']:
        page['size'] = len(page['content'])
