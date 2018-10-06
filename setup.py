import os
import setuptools


def all_data_files(path, excluded_dirs=()):
    for root, dirs, files in os.walk(path):
        for dir_ in dirs:
            if dir_ in excluded_dirs:
                dirs.remove(dir_)
        yield root, [os.path.join(root, file_) for file_ in files]


with open('README.md', 'r') as fd:
    long_description = fd.read()

setuptools.setup(
    name='obraz',
    version='0.9',
    author='Andrey Vlasovskikh',
    author_email='andrey.vlasovskikh@gmail.com',
    description='Static blog-aware site generator in Python mostly compatible '
                'with Jekyll',
    long_description=long_description,
    url='http://obraz.pirx.ru/',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Topic :: Internet :: WWW/HTTP :: Site Management',
    ],
    py_modules=['obraz'],
    install_requires=['PyYAML', 'Jinja2', 'Markdown', 'docopt'],
    entry_points={
        'console_scripts': [
            'obraz = obraz:main',
        ],
    },
    data_files=[(os.path.join('obraz', root), files)
                for root, files
                in all_data_files('scaffold', excluded_dirs=['_site'])])
