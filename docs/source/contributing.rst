.. _contributing:

Contributing
============

Bug reports and feature requests
--------------------------------

Bugs and new feature requests can be submitted to the `issue tracker on GitHub <https://github.com/cancervariants/metakb/issues>`_. See `this StackOverflow post <https://stackoverflow.com/help/minimal-reproducible-example>`_ for tips on how to craft a helpful bug report.

Development setup
-----------------

Clone the repository: ::

    git clone https://github.com/cancervariants/metakb
    cd metakb

Then initialize a virtual environment: ::

    python3 -m virtualenv venv
    source venv/bin/activate
    python3 -m pip install -e '.[dev,tests,docs,notebooks]'

We use `pre-commit <https://pre-commit.com/#usage>`_ to run conformance tests before commits. This provides checks for:

* Code format and style
* Added large files
* AWS credentials
* Private keys

Before your first commit, run: ::

    pre-commit install

Deployment
----------

Currently, the MetaKB is hosted for public access on [AWS Elastic Beanstalk](https://aws.amazon.com/elasticbeanstalk/). When a new Beanstalk container is launched, it does so from the dependencies declared in ``Pipfile.lock``. ::

  python -m pip install pipenv
  pipenv install --skip-lock  # this is what Elastic beanstalk uses

Style
-----

Code style is managed by `Ruff <https://github.com/astral-sh/ruff>`_, and should be checked via pre-commit hook before commits. Final QC is applied with GitHub Actions to every pull request.

Tests
-----

Tests are executed with `pytest <https://docs.pytest.org/en/7.1.x/getting-started.html>`_: ::

    pytest

Documentation
-------------

The documentation is built with Sphinx, which is included as part of the ``docs`` dependency group. Navigate to the ``docs/`` subdirectory and use ``make`` to build the HTML version: ::

    cd docs
    make html

See the `Sphinx documentation <https://www.sphinx-doc.org/en/master/>`_ for more information.
