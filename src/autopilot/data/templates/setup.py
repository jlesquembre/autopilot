from setuptools import setup, find_packages
import os
import re
import ast


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst'), 'rt') as f:
    README = f.read()

os.chdir(here)

_version_re = re.compile(r'__version__\s*=\s*(.*)')
with open(os.path.join(here, 'src/${project_name}', '__init__.py'), 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))


setup(name='${project_name}',
      version=version,
      author='${author}',
      author_email='${email}',
      description='Some description',
      long_description=README,
      license='${license_short}',
      #url='http://username.github.io/${project_name}}',
      packages=find_packages('src'),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      classifiers=[
        'License :: ${license_long}',
        'Programming Language :: Python',
        % for py_version in py_versions:
        'Programming Language :: Python :: ${py_version}',
        % endfor
        % if private:
        'Private :: Do Not Upload',
        % endif
        ],
      #entry_points={
      #    'console_scripts': [
      #        'myscript = ${project_name}.main:cli',
      #    ],
      #},
      #install_requires=['click']
    )
