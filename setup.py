"""Defines how metakb is packaged and distributed."""
from setuptools import setup

setup(name='metakb',
      version='0.0.0',
      description='Central repository for the VICC metakb web application',
      url='https://github.com/cancervariants/metakb',
      author='VICC',
      author_email='help@cancervariants.org',
      license='MIT',
      packages=['metakb'],
      zip_safe=False)
