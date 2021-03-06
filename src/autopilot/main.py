import os
import locale
import copy
import tempfile
import pprint

from pathlib import  Path
from contextlib import suppress

import click
import sarge

#from .scaffold import Options, InvalidOption, LICENSES, create_project, render
from . import render
from .ui import new_project_ui, release_ui
from . import utils
from . import git
from . import __version__

@click.group()
@click.version_option(__version__, prog_name='autopilot')
def cli():
    pass


@cli.command()
@click.argument('project_name', nargs=1, default='')
def new(project_name):
    """Creates a new project"""

    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        print("Warning: Unable to set locale.  Expect encoding problems.")

    config = utils.get_config()
    config['new_project']['project_name'] = project_name

    values = new_project_ui(config)
    if type(values) is not str:
        print('New project options:')
        pprint.pprint(values)
        project_dir = render.render_project(**values)
        git.init_repo(project_dir, **values)
    else:
        print(values)


@cli.command()
@click.option('--no-master', is_flag=True, default=False,
              help='By default, releases are allowed only from `master` branch. '
                   'This option disables that check')
@click.option('--type', 'release_type', show_default=True, help='Release type',
              type=click.Choice(['major', 'minor', 'patch']), default='patch')
def release(no_master, release_type):
    '''Releases a new version'''

    try:
        locale.setlocale(locale.LC_ALL, '')
    except:
        print("Warning: Unable to set locale.  Expect encoding problems.")

    git.is_repo_clean(master=(not no_master))

    config = utils.get_config()
    config.update(utils.get_dist_metadata())
    config['project_dir'] = Path(os.getcwd())
    config['release_type'] = release_type

    with tempfile.TemporaryDirectory(prefix='ap_tmp') as tmp_dir:
        config['tmp_dir'] = tmp_dir
        values = release_ui(config)

        if type(values) is not str:
            utils.release(project_name=config['project_name'], tmp_dir=tmp_dir,
                          project_dir=config['project_dir'],
                          pypi_servers=config['pypi_servers'], **values)

            print('New release options:')
            pprint.pprint(values)
        else:
            print(values)
