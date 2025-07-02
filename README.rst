|Latest Version| |Python| |License|

`csspin-python` is maintained and published by `CONTACT Software GmbH`_ and
serves Python-based plugins for the `csspin`_ task runner.

The following plugins are available:

- `csspin_python.behave`: A plugin for running tests using Behave.
- `csspin_python.debugpy`: A plugin for debugging Python code using `debugpy`_.
- `csspin_python.devpi`: A plugin for simplified usage of `devpi`_.
- `csspin_python.playwright`: A plugin for running tests using `playwright`_.
- `csspin_python.pytest`: A plugin for running tests using pytest.
- `csspin_python.python`: A plugin for provisioning Python environments  and
  installing dependencies.
- `csspin_python.radon`: A plugin for running `radon`_ to analyze code
  complexity.
- `csspin_python.sphinx`: A plugin for building Sphinx documentation.

The package provides an ``aws_auth`` extra, that, if enabled, can
authenticate to `CONTACT Software GmbH`_'s AWS Codeartifact.

Prerequisites
-------------

`csspin` is available on PyPI and can be installed using pip, pipx or any other
Python package manager, e.g.:

.. code-block:: console

   python -m pip install csspin

Using csspin-python
-------------------

The `csspin-python` package and its plugins can be installed by defining those
within the `spinfile.yaml` configuration file of your project.

.. code-block:: yaml

    spin:
      project_name: my_project

    # To develop plugins comfortably, install the packages editable as
    # follows and add the relevant plugins to the list 'plugins' below
    plugin_packages:
      - csspin-python

    # The list of plugins to be used for this project.
    plugins:
      - csspin_python.pytest

    python:
      version: 3.9.8
      requirements:
        - sphinx-click
        - sphinx-rtd-theme
        - pytest-mock

    pytest:
      opts: [-m, "not slow"]
      tests: [tests]

If the ``spinfile.yaml`` is configured correctly, you can provision the project
using ``spin provision``, that will automatically create a Python virtual
environment and install the required dependencies. After that, you can run
tests using ``spin pytest`` and do other great things.

.. _`CONTACT Software GmbH`: https://contact-software.com
.. |Python| image:: https://img.shields.io/pypi/pyversions/csspin-python.svg?style=flat
    :target: https://pypi.python.org/pypi/csspin-python/
    :alt: Supported Python Versions
.. |Latest Version| image:: http://img.shields.io/pypi/v/csspin-python.svg?style=flat
    :target: https://pypi.python.org/pypi/csspin/
    :alt: Latest Package Version
.. |License| image:: http://img.shields.io/pypi/l/csspin-python.svg?style=flat
    :target: https://www.apache.org/licenses/LICENSE-2.0.txt
    :alt: License
.. _`csspin`: https://pypi.org/project/csspin
.. _`debugpy`: https://pypi.org/project/debugpy
.. _`devpi`: https://pypi.org/project/devpi
.. _`playwright`: https://pypi.org/project/pytest-playwright
.. _`radon`: https://pypi.org/project/radon
