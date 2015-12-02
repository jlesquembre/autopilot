======================================
autopilot - Make Python packaging easy
======================================


    There should be one-- and preferably only one --obvious way to do it.

    -- The Zen of Python, by Tim Peters

There are too many options to create and distribute a Python package. Probably
that's why many people hate package distribution in Python:

.. raw:: html

    <iframe width="560" height="315"
        src="https://www.youtube.com/embed/bp3mCgrdMxU?rel=0&start=3360&end=3391"
        frameborder="0" allowfullscreen></iframe>

|
|

Autopilot tries to provide good defaults, avoiding you from repetitive tasks and
`bikeshedding <http://en.wikipedia.org/wiki/Parkinson's_law_of_triviality>`_.


Paradox of choice
-----------------

There are many choices when you create a Python package, but many of them are
choices on things that don't really matter. Just make the choice once and move
on. Conventions are good for things like choose where to store the version
number of your project. Nobody cares about it and don't thinking about it makes
you more productive. Autopilot makes this choices for you, and this way can
easily automate your package release. Of course, the choices are not written in
stone and can change over time, but the main idea is to change them only if
there is a good reason.

There is a talk from Yehuda Katz about defininig conventions, which I really recommend:

`Link to youtube <https://www.youtube.com/watch?v=9naDS3r4MbY>`_


On giants' shoulders
--------------------

These resources were an inspiration for autopilot:

- `Python Packaging User Guide <https://packaging.python.org/en/latest/>`_

- `Blog post from Ionel Cristian Mărieș <http://blog.ionelmc.ro/2015/02/24/the-problem-with-packaging-in-python/>`_

- `Zest.realeaser <http://zestreleaser.readthedocs.org/en/latest/>`_

.. http://www.drewblas.com/2008/05/31/railsconf-2008-friday-evening-summary/


**Contents:**

.. toctree::
   :maxdepth: 2

   self
   intro
   choices
   changelog



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
