import os
import sys
import logging
import json
import re

from pathlib import Path
from tempfile import TemporaryDirectory
#from contextlib import suppress

import requests

from mako.template import Template
from mako.lookup import TemplateLookup

from sarge import run, Capture

from . import utils


#log = logging.getLogger(__name__)
logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

PRIVATE_LICENSE_NAME = 'Other/Proprietary License'


def should_skip_file(name):
    """
    Checks if a file should be skipped based on its name.

    If it should be skipped, returns the reason, otherwise returns
    None.
    """
    if name.endswith(('~', '.bak')):
        return 'Skipping backup file %(filename)s'
    if name.endswith(('.pyc', '.pyo')):
        return 'Skipping %s file ' % os.path.splitext(name)[1] + '%(filename)s'
    if name.endswith('$py.class'):
        return 'Skipping $py.class file %(filename)s'
    return None


def render_project(directory, project_name, license, version='0.0.1.dev0', py_versions=('3', '3.5'), **kwargs):

    # Create project directory
    try:
        project_dir = Path(directory) / project_name
        project_dir.mkdir()
    except FileExistsError:
        print('Directory "{}" already exits in "{}"!!!'.format(project_name, directory))
        sys.exit(1)

    license_variables = process_license(license)
    license_dir = license_variables.pop('license_dir')

    # Render the templates
    variables = {'project_name': project_name,
                 'py_versions': py_versions,
                 'version': version,
                 'author': kwargs.get('user_name'),
                 'email': kwargs.get('user_email'),
                 **license_variables
                 }

    templates_dir = utils.get_data_dir() / 'templates'
    lookup = TemplateLookup(directories=[templates_dir.as_posix(), license_dir.name],
                            module_directory='/tmp/autopilot_mako_modules',
                            output_encoding='utf-8', input_encoding='utf-8',
                            encoding_errors='replace')

    for level, (path, subdirs, files) in enumerate(os.walk(templates_dir.as_posix())):
        path = Path(path)
        if '__pycache__' in subdirs:
            subdirs.remove('__pycache__')

        if level == 0:   # Inject license, it was generated
            files.append('LICENSE')
        for name in files:
            if should_skip_file(name):
                continue

            in_path = (path / name).relative_to(templates_dir)
            # Get output path to render the template
            out_path = Template((project_dir / in_path).as_posix(),
                            #output_encoding='utf-8', input_encoding='utf-8',
                            encoding_errors='replace').render_unicode(**variables)
            out_path = Path(out_path)
            #logging.info('Render {}'.format(out_path.relative_to(project_dir)))
            print('Render {}'.format(out_path.relative_to(project_dir)))

            out_path.parent.mkdir(parents=True, exist_ok=True)

            template = lookup.get_template(in_path.as_posix())
            with out_path.open(mode='xb') as out:
                out.write(template.render(**variables))

    license_dir.cleanup()
    return project_dir

def process_license(name):

    license_in = utils.get_data_dir() / 'licenses' / name
    if not license_in.exists():
        license_in = utils.get_user_config_dir() / 'licenses' / name

    long_name = PRIVATE_LICENSE_NAME

    just_write = False
    re_whites = re.compile(r'^\s*$')
    re_license = re.compile(r'\s*#\s*pypi\s*license\s*:\s*(.+)\n')

    license_out_dir = TemporaryDirectory()
    license_out = Path(license_out_dir.name) / 'LICENSE'

    with license_in.open('rt') as f_in, license_out.open('w+t') as f_out:
        for line in iter(f_in.readline, ''):  # Like readlines, but with a generator
            if just_write:
                f_out.write(line)
            else:
                if re_whites.match(line):
                    continue
                m = re_license.match(line)
                if m:
                    long_name = m.group(1)
                    continue

                # We didn't match anything, this is the file start
                f_out.write(line)
                just_write = True

    long_name, private = _parse_license_name(long_name)

    return {'private': private,
            'license_short': name,
            'license_long': long_name,
            'license_dir': license_out_dir,
            }


def _parse_license_name(long_name):
    ''' Check if the license name on the PyPI licenses list. Prepends 'OSI
    Approved :: ' if required. If the license is 'Other/Proprietary License' or
    unknow, asummes that is a private license.
    '''
    licenses_path = utils.get_data_dir() / 'license_list.txt'
    with licenses_path.open('rt') as f:
        licenses = [line.strip() for line in f.readlines()]

    if long_name in licenses:
        return long_name, long_name == PRIVATE_LICENSE_NAME

    osi_name = 'OSI Approved :: {}'.format(long_name)
    if osi_name in licenses:
        return osi_name, False

    logging.warn('License "{}" is not a valid PyPI classifier'.format(long_name))

    return long_name, True
