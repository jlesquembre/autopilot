import os

from contextlib import contextmanager

import git.exc
from git import Repo

from .exceptions import FatalError


def init_repo(path, **kwargs):
    repo = Repo.init(str(path))
    repo.index.add(repo.untracked_files)

    cw = repo.config_writer()
    cw.set_value('user', 'name', kwargs.get('user_name', ''))
    cw.set_value('user', 'email', kwargs.get('user_email', ''))
    cw.release()

    if kwargs.get('initial_commit'):
        print('Do initial commit...')
        repo.index.commit('Initial commit')
    else:
        print('Next step:')
        print('git commit -m "Initial commit"')


def is_repo_clean(repo_path=None, master=True):
    try:
        path = repo_path if repo_path else os.getcwd()
        repo = Repo(path)
    except git.exc.InvalidGitRepositoryError:
        raise FatalError('ERROR: No git repository found at "{}"'.format(path))

    if master and repo.active_branch.name != 'master':
        raise FatalError('ERROR: Usually your active branch should be master'
                         ' before you do a new release.\n'
                         'If you are sure you want to do a release from this'
                         ' branch, use the "--no-master" flag:\n\n'
                         'ap release --no-master\n')

    if repo.is_dirty():
        raise FatalError('ERROR: Your working tree contains modifications'
                         ' which have not been committed')


@contextmanager
def checkout_tag(repo, tag):
    branch = repo.active_branch.name
    repo.git.checkout(tag)
    try:
        yield
    finally:
        repo.git.checkout(branch)


def git_push(repo, last_tag):
    try:
        repo.remote().push(['refs/heads/*', 'refs/tags/*'])
    except:
        # Other way to get the last tag:
        # last_tag = sorted(repo.tags, key=lambda t: t.commit.committed_date)[-1].name
        repo.delete_tag(last_tag)
        # git reset --hard
        repo.head.reset('HEAD~2', index=True, working_tree=True)

        raise FatalError(
            'Error pushing changes to remote. Abort release and undo changes.')
