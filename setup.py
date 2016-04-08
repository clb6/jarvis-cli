from setuptools import setup, find_packages

setup(name = "jarvis", version = "0.3.0", packages = find_packages(),
        author = "Michael Hwang", author_email = "hirehwnag@gmail.com",
        description = ("Jarvis python client"), scripts=['bin/jarvis.py'],
        install_requires=['requests', 'tabulate'], zip_safe = False)
