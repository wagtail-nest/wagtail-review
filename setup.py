#!/usr/bin/env python

from setuptools import setup, find_packages

setup(
    name='wagtail-review',
    version='0.5',
    description="Review workflow for Wagtail",
    author='Matthew Westcott',
    author_email='matthew.westcott@torchbox.com',
    url='https://github.com/wagtail-nest/wagtail-review',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'swapper>=1.1,<1.2',
    ],
    python_requires=">=3.8",
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
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Framework :: Django',
        'Framework :: Django :: 4.2',
        'Framework :: Django :: 5.0',
        'Framework :: Django :: 5.1',
        'Framework :: Wagtail',
        'Framework :: Wagtail :: 4',
        'Framework :: Wagtail :: 5',
        'Framework :: Wagtail :: 6',
    ],
)
