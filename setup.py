from setuptools import setup, find_packages
from jarvis_cli import __version__

setup(
        name = "jarvis-cli",
        version = __version__,
        packages = find_packages(),
        author = "Michael Hwang",
        author_email = "hirehwang@gmail.com",
        description = ("Jarvis command-line tool"),
        # Adopted the method of creating bins through setuptools
        # http://click.pocoo.org/5/setuptools/#setuptools-integration
        # The webpage lists benefits of doing this.
        entry_points="""
        [console_scripts]
        jarvis=jarvis_cli.commands:cli
        """,
        install_requires=['requests', 'tabulate', 'dateparser<1.0.0', 'click<7.0'],
        zip_safe = False
        )
