import tempfile

from pathlib import Path

import pytest

from git import Repo
from sarge import capture_stdout, run

from autopilot import git
from autopilot.exceptions import FatalError


def test_init_repo(dir_with_file):
    git.init_repo(dir_with_file)

    p = capture_stdout('git ls-files', cwd=str(dir_with_file))
    assert p.stdout.text == 'readme.txt\n'

    p = capture_stdout('git config --get user.name', cwd=str(dir_with_file))
    assert p.stdout.text == '\n'

    p = capture_stdout('git config --get user.email', cwd=str(dir_with_file))
    assert p.stdout.text == '\n'

    p = capture_stdout('git rev-list --all --count', cwd=str(dir_with_file))
    assert p.returncode != 0
    assert p.stdout.text == ''


def test_init_repo_with_user(dir_with_file):
    git.init_repo(dir_with_file, initial_commit=True,
                  user_name='John', user_email='john@test.org')

    p = capture_stdout('git ls-files', cwd=str(dir_with_file))
    assert p.stdout.text == 'readme.txt\n'

    p = capture_stdout('git config --get user.name', cwd=str(dir_with_file))
    assert p.stdout.text == 'John\n'

    p = capture_stdout('git config --get user.email', cwd=str(dir_with_file))
    assert p.stdout.text == 'john@test.org\n'

    p = capture_stdout('git rev-list --all --count', cwd=str(dir_with_file))
    assert p.stdout.text == '1\n'


def test_is_repo_clean(git_dir):
    assert git.is_repo_clean(repo_path=str(git_dir)) is None

    new_file = git_dir / 'new_file.txt'
    with new_file.open('w') as f:
        f.write('Some text')

    run('git add new_file.txt', cwd=str(git_dir))
    with pytest.raises(FatalError) as excinfo:
        git.is_repo_clean(repo_path=str(git_dir))
    assert 'working tree contains modifications' in str(excinfo.value)


def test_is_repo_clean_no_repo(dir_with_file):
    with pytest.raises(FatalError) as excinfo:
        git.is_repo_clean(repo_path=str(dir_with_file))
    assert 'No git repo' in str(excinfo.value)


def test_is_repo_clean_no_master(git_dir):
    run('git checkout -b new_branch', cwd=str(git_dir))

    with pytest.raises(FatalError) as excinfo:
        git.is_repo_clean(repo_path=str(git_dir))
    assert 'branch should be master' in str(excinfo.value)

    assert git.is_repo_clean(repo_path=str(git_dir), master=False) is None


def test_git_checkout_tag(git_dir):

    run('git tag v1', cwd=git_dir.as_posix())

    new_file = git_dir / 'new_file.txt'
    with new_file.open('w') as f:
        f.write('Some text')
    run('git add {}'.format(new_file), cwd=git_dir.as_posix())
    run('git commit -m "message"', cwd=git_dir.as_posix())

    assert new_file.exists() is True

    with git.checkout_tag(Repo(git_dir.as_posix()), 'v1'):
        assert new_file.exists() is False

    assert new_file.exists() is True


def test_git_push(git_dir):

    with tempfile.TemporaryDirectory() as tempdir:

        bare_dir = Path(tempdir)
        run('git --bare init', cwd=bare_dir.as_posix())
        run('git remote add origin {}'.format(bare_dir), cwd=git_dir.as_posix())
        run('git push --set-upstream origin master', cwd=git_dir.as_posix())

        # create tag, add file and do commit
        run('git tag v1', cwd=git_dir.as_posix())
        new_file = git_dir / 'new_file.txt'
        with new_file.open('w') as f:
            f.write('Some text')
        run('git add {}'.format(new_file), cwd=git_dir.as_posix())
        run('git commit -m "message"', cwd=git_dir.as_posix())

        git.git_push(Repo(git_dir.as_posix()), 'v1')

        p = capture_stdout('git ls-tree -r HEAD --name-only', cwd=str(bare_dir.as_posix()))
        files = p.stdout.text.splitlines()

        assert 'new_file.txt' in files

        p = capture_stdout('git describe --abbrev=0 --tags', cwd=bare_dir.as_posix())
        assert p.stdout.text == 'v1\n'
