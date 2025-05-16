import os
from setuptools import setup, find_packages

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "poker-game",
    version = "0.0.4",
    author = "Dave",
    author_email = "davidus27@gmail.com",
    description = ("Small summer project to escape from the boredom"),
    license = "GNU",
    keywords = "poker game",
    url = "http:/github.com/davidus27/pokerGame",
    packages=find_packages(),
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Games/Entertainment",
        "License :: OSI Approved :: GNU License",
    ],
    python_requires='>=3.6',
)
