#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='wagtail-review',
    version='0.3',
    description="Review workflow for Wagtail",
    author='Matthew Westcott',
    author_email='matthew.westcott@torchbox.com',
    url='https://github.com/wagtail/wagtail-review',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'swapper>=1.1,<1.2',
    ],
    license='BSD',
    long_description="An extension for Wagtail allowing pages to be submitted for review (including to non-Wagtail users) prior to publication",
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Framework :: Django',
        'Framework :: Wagtail',
        'Framework :: Wagtail :: 2',
    ],
)
