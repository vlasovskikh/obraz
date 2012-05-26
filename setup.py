from setuptools import setup

setup(
    name='obraz',
    version='0.1',
    packages=['test'],
    py_modules=['obraz'],
    requires=['PyYAML', 'Jinja2', 'Markdown'],
    entry_points={
        'console_scripts': [
            'obraz = obraz:main',
        ],
    },
    url='http://obraz.pirx.ru/',
    license='MIT',
    author='Andrey Vlasovskikh',
    author_email='andrey.vlasovskikh@gmail.com',
    description='Static site generator in a single Python file similar to Jekyll')

