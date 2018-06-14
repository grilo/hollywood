#!/usr/bin/env python

"""
    Hollywood - Basic actor framework.
"""

import os
from setuptools import setup, find_packages


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="hollywood",
    version="0.1",
    author="Joao Grilo",
    author_email="joao.grilo@gmail.com",
    description="Basic actor framework",
    license="BSD",
    keywords="actor framework",
    url="https://github.com/grilo/hollywood",
    packages=find_packages(),
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: BSD License",
    ],
    setup_requires=['pytest-runner'],
    tests_require=['pylint', 'pytest', 'pytest-cov', 'pytest-mock'],
)
