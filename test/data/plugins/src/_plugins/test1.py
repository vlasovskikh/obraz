from __future__ import unicode_literals
import csv
import os
import obraz


@obraz.loader
def load_capitals(path, site):
    test1_site = site.get('test1', {})
    capitals_filename = test1_site.get('capitals_filename', 'capitals.csv')
    if path != capitals_filename:
        return None
    with open(os.path.join(site['source'], path), 'r') as fd:
        reader = csv.reader(fd)
        capitals = dict((country, capital) for capital, country in reader)
    return {
        'test1': {
            'capitals': capitals,
        }
    }

@obraz.processor
def process_size(site):
    for page in site.get('pages', {}):
        page['size'] = len(page['content'])


@obraz.generator
def generate_capitals_count_file(site):
    name = os.path.join(site['destination'], 'capitals_count.txt')
    with open(name, 'wb') as fd:
        capitals = site.get('test1', {}).get('capitals', {})
        data = '{0}\n'.format(len(capitals)).encode('UTF-8')
        fd.write(data)
