#!/usr/bin/env python
from distutils.core import setup
import os.path
import tempfile

selfdir = os.path.dirname(os.path.realpath(__file__))

alppy = open(os.path.join(selfdir, 'alp.py'))
alpname = os.path.join(tempfile.gettempdir(), 'alp')
alp = open(alpname, 'w')
alp.write(alppy.read())
alppy.close()
alp.close()

readme = open(os.path.join(selfdir, 'README.txt')).read()
conf = dict(
    name='Alp',
    version='0.1.1',
    author='Niels Serup',
    author_email='ns@metanohi.org',
    package_dir={'': '.'},
    py_modules = ['alp'],
    scripts=[alpname],
    url='http://metanohi.org/projects/alp/',
    license='GPLv3+',
    description='Alp time tools',
    classifiers=['Development Status :: 4 - Beta',
                 'Intended Audience :: End Users/Desktop',
                 'Intended Audience :: Developers',
                 'Topic :: Software Development :: Libraries :: Python Modules',
                 'Topic :: Utilities',
                 'Environment :: Console',
                 'License :: OSI Approved :: GNU General Public License (GPL)',
                 'License :: DFSG approved',
                 'Operating System :: OS Independent',
                 'Programming Language :: Python'
                 ]
)

try:
    # setup.py register wants unicode data..
    conf['long_description'] = readme.decode('utf-8')
    setup(**conf)
except Exception:
    # ..but setup.py sdist upload wants byte data
    conf['long_description'] = readme
    setup(**conf)
