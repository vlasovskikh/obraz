from setuptools import setup

setup(
    name='obraz',
    version='0.3',
    packages=['test'],
    py_modules=['obraz'],
    install_requires=['PyYAML', 'Jinja2', 'Markdown', 'docopt'],
    entry_points={
        'console_scripts': [
            'obraz = obraz:main',
        ],
    },
    url='http://obraz.pirx.ru/',
    license='MIT',
    author='Andrey Vlasovskikh',
    author_email='andrey.vlasovskikh@gmail.com',
    description='Static site generator in a single Python file similar to '
                'Jekyll')
