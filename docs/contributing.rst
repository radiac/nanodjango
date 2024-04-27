============
Contributing
============

Development
===========

First, fork the ``nanodjango`` project on GitHub. If you haven't done this before, look for the Fork button in the upper right corner of the project's [home page](https://github.com/radiac/nanodjango/). This will copy the main branch of the project to a new repository under your account.

Next, clone your new repository (replace ``<username>`` with your username) to your local machine:

.. code-block:: bash
    $ git clone git@github.com:<username>/nanodjango.git

If this doesn't work, try this alternative:

.. code-block:: bash
    $ git clone https://github.com/<username>/nanodjango.git

Add an ``upstream`` remote, then configure ``git`` to pull ``main`` from ``upstream`` and always push to ``origin`:

.. code-block:: bash
    $ cd nanodjango
    nanodjango$ git remote add upstream https://github.com/radiac/nanodjango
    nanodjango$ git config branch.main.remote upstream
    nanodjango$ git remote set-url --push upstream git@github.com:<your-username>/nanodjango.git

This makes sure you'll be able to pull changes from the upstream nanodjango project, while pushing your changes to your fork.

You can verify that ``git`` is configured correctly by running:

.. code-block:: bash
    nanodjango$ git remote -v
    origin  git@github.com:<username>/nanodjango.git (fetch)
    origin  git@github.com:<username>/nanodjango.git (push)
    upstream        https://github.com/radiac/nanodjango (fetch)
    upstream        git@github.com:<username>/nanodjango.git (push)
    nanodjango$ git config branch.main.remote
    upstream

If you did everything correctly, you should now have a copy of the code in the ``nanodjango`` directory and two remotes that refer to your own GitHub fork (`origin`) and the official nanodjango repository (`upstream`).

Now create a virtual environment and install the necessary dependencies:

For macOS and Linux:

.. code-block:: bash
    nanodjango$ python -m venv .venv
    nanodjango$ source .venv/bin/activate
    (.venv) nanodjango$ pip install --upgrade pip
    (.venv) nanodjango$ pip install -r requirements.txt

For Windows:

.. code-block: bash
    nanodjango> python -m venv .venv
    nanodjango> .venv\Scripts\activate
    (.venv) nanodjango> pip install --upgrade pip
    (.venv) nanodjango> pip install -r requirements.txt
    
Now you should have all the dependencies installed to run the project.

Running examples
================

Then run examples by adding your ``nanodjango`` dir to the ``PYTHONPATH``, and call
the repo module directly::

    cd examples
    PYTHONPATH=.. python -m nanodjango counter.py run migrate

Running tests
=============

Install dependencies that are only required for tests, and run tests:

.. code-block:: bash
    (.venv) nanodjango$ pip install -r tests/requirements.txt
    (.venv) nanodjango$ pytest

Submitting a PR
===============

Before making a pull request, please open an issue to discuss the change you'd like to make. This will help ensure we're working on a shared vision for the project.

Assuming you've set up your fork as described above, use the following workflow to implement a feature or a bugfix:

* Make sure you have pulled any recent changes from the upstream fork.
* Make a new branch on your fork.
* Commit your changes on your fork.
* Push your branch to your fork.
* Open a PR:
    * If you see a button to submit a PR based on this fork on the main page of your fork, you can click that button.
    * If you don't see that button on your fork's main page, click the branches dropdown and click on the relevant branch.
* Fill out the pull request, making sure it's going to submit your fork to the upstream repository.

Merging upstream changes to your fork
=====================================

The upstream project is going to get ahead of your fork. Take these steps to pull changes from the main upstream repository to your fork:

.. code-block:: bash
    $ git checkout main
    $ git fetch upstream
    $ git merge upstream/main
    $ git push origin main

This first makes sure you're on your fork's main branch. It then fetches the latest changes from the upstream project. It merges those changes into your main branch, and finally pushes those updates back to your fork.

Building documentation
======================

To build a local copy of the documentation:

.. code-block:: bash
    (.venv) nanodjango$ pip install -r docs/requirements.txt
    (.venv) nanodjango$ cd docs
    (.venv) docs$ make html

You'll find a set of freshly-generated HTML files in `docs/_build/html/`.

Getting help
============

If you're trying to contribute and these steps aren't working for you, please open an issue and let us know what specific step is not working.

Thanks
======

Thanks to `Remix Icon <https://remixicon.com/>`_ for the example icon.
