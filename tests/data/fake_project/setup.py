from setuptools import setup, find_packages
import os
import re
import ast


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), 'rt') as f:
    README = f.read()

os.chdir(here)

_version_re = re.compile(r'__version__\s*=\s*(.*)')
with open(os.path.join(here, 'src/fake_project', '__init__.py'), 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


setup(name='fake_project',
      version=version,
      author='John Doe',
      author_email='username@test.com',
      description='Some description',
      long_description=README,
      license='GPLv2',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      classifiers=[
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        ],
    )
