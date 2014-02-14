import os
from setuptools import setup


def all_data_files(path, excluded_dirs=()):
    for root, dirs, files in os.walk(path):
        for dir_ in dirs:
            if dir_ in excluded_dirs:
                dirs.remove(dir_)
        yield root, [os.path.join(root, file_) for file_ in files]


setup(
    name='obraz',
    version='0.9',
    py_modules=['obraz'],
    install_requires=['PyYAML', 'Jinja2', 'Markdown', 'docopt'],
    entry_points={
        'console_scripts': [
            'obraz = obraz:main',
        ],
    },
    data_files=[(os.path.join('obraz', root), files)
                for root, files
                in all_data_files('scaffold', excluded_dirs=['_site'])],
    url='http://obraz.pirx.ru/',
    license='MIT',
    author='Andrey Vlasovskikh',
    author_email='andrey.vlasovskikh@gmail.com',
    description='Static site generator in a single Python file mostly '
                'compatible with Jekyll')
