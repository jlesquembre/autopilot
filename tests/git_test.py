import pytest

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
    assert git.is_repo_clean(repo_path=str(git_dir)) == None

    new_file = git_dir / 'new_file.txt'
    with new_file.open('w') as f:
        f.write('Some text')

    p = capture_stdout('git add new_file.txt', cwd=str(git_dir))
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

    assert git.is_repo_clean(repo_path=str(git_dir), master=False) == None