from setuptools import setup, find_packages
import os
import re
import ast
import sys


if sys.version_info < (3, 5):
    sys.exit("Sorry, autopilot only supports Python 3.5 or better")


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), 'rt') as f:
    README = f.read()

os.chdir(here)

_version_re = re.compile(r'__version__\s*=\s*(.*)')
with open(os.path.join(here, 'src/autopilot', '__init__.py'), 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(name='autopilot',
      version=version,
      author='José Luis Lafuente',
      author_email='jl@lafuente.me',
      description='blabla',
      long_description=README,
      license='GNU General Public License v2 (GPLv2)',
      url='http://jlesquembre.github.io/autopilot',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      classifiers=[
        'Development Status :: 3 - Alpha',
        'Topic :: Utilities',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.5',
        ],
      keywords=['python'],
      entry_points = {
          'console_scripts': [
              'ap = autopilot.main:cli',
          ],
          'setuptools.file_finders': [
              'git = autopilot.utils:setuptools_file_finder'
          ],
      },
      install_requires=['click>=5.1',
                        'distlib>=0.2.1',
                        'GitPython>=1.0.1',
                        'Mako>=1.0.2',
                        #'PyYAML>=3.11',
                        'ruamel.yaml>=0.10.7',
                        'sarge>=0.1.4',
                        'twine==1.5.0',
                        ]
    )
