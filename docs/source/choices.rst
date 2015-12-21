=======
Choices
=======


Structure
---------

In our top level directory, we have the following folders:

    - src/${project_name}

        .. note::

            This way you get import parity, see http://blog.ionelmc.ro/2014/05/25/python-packaging/#the-structure

            .. # In a perfect world, this directory would be called `src`, but later we can import the package with an `import ${project_name}`

    - docs

    - tests


And the following files:

    - setup.py

    - README.rst

    - CHANGELOG.rst

    - LICENSE

    - .gitignore

    - requirements.txt

        .. note::

            Here you have your dev requirements


    - setup.cfg

        .. note::

            This file is for external utilities configuration


    - tox.ini

        .. note::

            .. TODO Move to other section
            Test both with coverage measurements and without. See http://blog.ionelmc.ro/2014/05/25/python-packaging/#tl-dr
            For coverage we do a `pip install -e`, but test with a normal pip install are also great.


    - .travis.yml

        .. note::

            .. TODO Move to other section
            Use tox file here.




Project version
---------------

In your ``src/${project_name}/__init__.py`` file. We can extract it later using
regex on our `setup.py`. But it is also possible to get the version number in
our python code:

::

    >>> import autopilot
    >>> autopilot.__version__
    '0.2.1'



Git workflow
------------

http://endoflineblog.com/gitflow-considered-harmful


License
-------

Autopilot includes some default licenses, like `GPLv2` or `MIT`. You need to
choose one, which would be copied into the `LICENSE` file, at the top directory
of your project. There is an special type of license, `Private`. This one
doesn't add a license file (well, it creates a `LICENSE` file, but is just link
to the `GNU licenses website
<http://www.gnu.org/licenses/license-list.en.html#NoLicense>`_). This license
also adds a classifier to your package, "Private :: Do Not Upload".  PyPI will
refuse to accept packages with unknown classifiers, hence we want to use it for
private packages to protect ourselves from a mistake. Anyways, if we have a
private devpi_ we still can upload the package there.


If you want to add a new license to the list of licenses, put the license file
at `$XDG_CONFIG_HOME/autopilot/licenses` directory (usually
`~/.config/autopilot/licenses`). Filename would be used to generate the
selectable list of licenses.  By default, user licenses are private, and the
`Private` classifier would be added to your `setup.py`. If you want to change
this behavior, the first line of your license must be like this:

.. code-block:: text

    # pypi license: License name

where license name must be a valid license name listed here: :doc:`license_list`

The list was extracted from `PyPI list of classifiers
<https://pypi.python.org/pypi?%3Aaction=list_classifiers>`_. For the OSI
licenses you can remove `'OSI Approved ::'` from the license name.


That first line, and all the empty lines after them, are not copied to your `LICENSE` file.


Changelog
---------

You should maintain a changelog file (`CHANGELOG.rst`). When you do a new
release, it is possible to open the changelog with a text editor, but any
changes you do to the file, would be discarded. For that reason, is recommended
to open the editor in read-only mode. If you use vim, you can set the editor to
`vim -R` on your local autopilot configuration::

    editor: vim -R

.. _devpi: http://doc.devpi.net/latest/
