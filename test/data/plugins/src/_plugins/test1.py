import csv
import os
import obraz


@obraz.loader
def load_capitals(basedir, filename, site):
    test1_site = site.get('test1', {})
    capitals_filename = test1_site.get('capitals_filename', 'capitals.csv')
    if filename != capitals_filename:
        return None
    path = os.path.join(basedir, filename)
    with open(path, 'r') as fd:
        reader = csv.reader(fd)
        test1_site['capitals'] = dict((country, capital)
                                      for capital, country in reader)


@obraz.processor
def process_size(basedir, destdir, site):
    for page in site['pages']:
        page['size'] = len(page['content'])


@obraz.generator
def generate_capitals_count_file(basedir, destdir, site):
    name = os.path.join(destdir, 'capitals_count.txt')
    with open(name, 'wb') as fd:
        capitals = site.get('test1', {}).get('capitals', {})
        data = '{0}\n'.format(len(capitals)).encode('UTF-8')
        fd.write(data)
