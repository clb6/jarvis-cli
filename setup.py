from setuptools import setup, find_packages
from jarvis_cli import __version__

setup(
        name = "jarvis-cli",
        version = __version__,
        packages = find_packages(),
        author = "Michael Hwang",
        author_email = "hirehwnag@gmail.com",
        description = ("Jarvis command-line tool"),
        scripts=['bin/jarvis.py'],
        install_requires=['requests', 'tabulate', 'dateparser<1.0.0'],
        zip_safe = False
        )
