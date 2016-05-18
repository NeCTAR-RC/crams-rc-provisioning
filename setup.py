#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

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
    install_requires=[
                      "python-dateutil==2.4.2",
                      "python-ceilometerclient==2.1.0",
                      "python-cinderclient==1.5.0",
                      "python-heatclient==0.8.0",
                      "python-keystoneclient==2.0.0",
                      "python-neutronclient==3.1.0",
                      "python-novaclient==2.35.0",
                      "python-saharaclient==0.11.1",
                      "python-swiftclient==2.6.0",
                      "python-troveclient==1.4.0",
                      "simplejson==3.8.1",
                      "urllib3==1.14",
                      ],
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
)
