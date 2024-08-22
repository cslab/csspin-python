.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_python.python:

==================
spin_python.python
==================

The ``spin_python.python`` plugin is the core plugin of the ``spin_python``
plugin-package. It is not only used for creating a virtual environment which
serves as location for all spin-related tooling and plugin-dependencies, it also
enables the dynamic installation and access of/to tools.

Please note that the ``spin_python.python`` plugin is required and used by all
plugins within the ``spin_python`` plugin-package.

How to setup the ``spin_python.python`` plugin?
###############################################

For using the ``spin_python.python`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``spin_python.python``

    minimum-spin: "0.2"
    plugin-packages:
        - spin_python
    plugins:
        - spin_python.python
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin --provision``-command.

How to install packages from another package index and sources?
###############################################################

The default index for installing Python packages is
https://packages.contact.de/tools/stable ensuring to install packages provided
by CONTACT first. To add another index, for example a dev-index for the
development of CE16 components, the configuration of pip can be adjusted by
extending the project's ``spinfile.yaml`` like this:

.. code-block:: yaml
    :caption: Using a custom index URL, e.g. for installing cs-packages

    ...
    python:
        version: "3.11.9"
        pipconf:
            global:
                # The PyPI index to get the cs-packages from
                index-url: https://packages.contact.de/apps/16.0-dev/+simple/

        # Additional requirements can be used to install further Python-packages
        # into the virtual environment created by the spin_python.python plugin.
        requirements:
            - cs.admin
            - cs.platform[postgres]

How to install packages from other sources instead from the package server?
###########################################################################

Installing a package from a local file system in editable mode can be done by
adding the path to the desired package prefixed with ``-e`` to the
``devpackages`` key in the project's ``spinfile.yaml``:

.. code-block:: yaml
    :caption: Installing additional, editable packages from other sources than a package server

    ...
    python:
        version: "3.11.9"
        ...
        # The 'devpackages' key can be used like below to install certain
        # packages from local sandboxes or elsewhere instead from the package
        # server used.
        devpackages:
            - -e cs.templatetest

How to use an existing Python interpreter, instead of provisioning another one?
###############################################################################

Sometimes downloading and installing a Python interpreter can be annoying, in
case there is already an existing interpreter that should be used in the context
of cs.spin. For this case, the configuration tree property ``python.use`` can be
set via command-line, the environment or within ``spinfile.yaml`` to enforce the
usage of the passed interpreter.

.. code-block:: console
    :caption: Using an existing Python interpreter

    spin -p python.use=python --provision
    ...
    spin -p python.use=/usr/bin/python <task>

How to activate the virtual environment provisioned by cs.spin manually?
########################################################################

Retrieving the path to activate the virtual environment created by the
``spin_python.python`` plugin is as easy as follows:

.. code-block:: console
    :caption: Retrieving the activate script of the virtual environment provisioned by cs.spin

    # Unix-style shells:
    spin env
    . /home/bts/src/qs/spin/spin_python/.spin/venv/bin/activate

    # Powershell 7:
    spin env
    C:\Users\buildbot\Desktop\cs.spin\.spin\venv\Scripts\activate.ps1

Activating the virtual environment can be done by sourcing the activate script:

.. code-block:: console
    :caption: Activating the virtual environment provisioned by cs.spin

    # Unix-style shells:
    $(spin env)

    # Powershell 7:
    & (spin env)

How to modify the behavior of the installation of the current package?
######################################################################

The behavior to install the current package can be modified in two ways.

One is, to include optional dependencies (so called :emphasis:`extras`) of the current package.
This can be done in the spinfile.yaml like this:

.. code-block:: yaml
    :caption: Include the extras ``postgres`` and ``s3`` during provisioning

    ...
    python:
        current_package:
            extras:
                - postgres
                - s3

Please note, that this only ever works, when the current package has these extras defined.

The other way is to not install the current package during provisioning. This could be handy
if only tasks should be run, that don't need the current package installed in the venv.
To do so, add the following to your ``spinfile.yaml``:

.. code-block:: yaml
    :caption: Suppress the installation of the current python package

    ...
    python:
        current_package:
            install: False

``spin_python.python`` schema reference
#######################################

.. include:: python_schemaref.rst
