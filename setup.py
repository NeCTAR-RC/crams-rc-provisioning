#!/usr/bin/env python
# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from pip.req import parse_requirements


requirements = parse_requirements("requirements.txt", session=False)
readme = open('README').read()

setup(
    name='crams_provision',
    version='0.1.0',
    description='crams nectar provision',
    long_description=readme,
    author='Simon Yu, Melvin Luong, mohamed feroze',
    author_email='xm.yuau@gmail.com, melvin.luong@monash.edu, mohamed.feroze@monash.edu',
    url='https://github.com/NeCTAR-RC/crams-rc-provisioning',
    platforms='Linux, Mac OS',
    packages=find_packages(exclude=['tests', 'local']),
    include_package_data=True,
    install_requires=[str(r.req) for r in requirements],
    license="GPLv3+",
    zip_safe=False,
    keywords='crams_provision',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v3 or '
        'later (GPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3.5',
        'Operating System :: OS Independent',
    ],
    entry_points="""
    # -*- Entry points: -*-
    [console_scripts]
    crams-provision-nectar = crams_provision.provision:main
    """,
)
