.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   https://www.contact-software.com/

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

.. _csspin_python.python:

====================
csspin_python.python
====================

The ``python`` plugin is the core plugin of the ``csspin-python``
plugin-package. It is not only used for creating a virtual environment which
serves as location for all spin-related tooling and plugin-dependencies, it also
enables the dynamic installation and access of/to tools.

Please note that the ``python`` plugin is required and used by all
plugins within the ``csspin-python`` plugin-package.

How to setup the ``python`` plugin?
###################################

For using the ``python`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``python``

    plugin_packages:
        - csspin-python
    plugins:
        - csspin_python.python
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

How to install packages from another package index and sources?
###############################################################

Using a static index URL
~~~~~~~~~~~~~~~~~~~~~~~~

The default index for installing Python packages is https://pypi.org/simple. To
be able to install packages from another index, for example the dev-index for
the development of CE16 components, the plugin's configuration can be adjusted
by extending the project's ``spinfile.yaml`` like this:

.. code-block:: yaml
    :caption: Using a custom index URL, e.g. for installing cs-packages

    ...
    python:
        version: "3.11.9"
        index_url: <URL to retrieve the CE packages from>

        # Additional requirements can be used to install further Python-packages
        # into the virtual environment created by the python plugin.
        requirements:
            - cs.admin
            - cs.platform[postgres]

Using AWS Codeartifact Repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

csspin-python provides an extra named ``aws_auth`` that installs the
command-line tool `csaccess`_ to authenticate with the AWS
Codeartifact Python package index for CONTACT Software GmbH.

To install csspin-python using this extra make sure it is enabled in the project's
``spinfile.yaml``:

.. code-block:: yaml
    :caption: ``spinfile.yaml`` enabling csspin-python[aws_auth]

    ...
    plugin_packages:
        - csspin-python[aws_auth]

    python:
        aws_auth:
            enabled: True
    ...

When provisioning a project using the extra installed *and* enabled, make sure
to have the following environment variables in place:

- ``CS_AWS_OIDC_CLIENT_ID``
- ``CS_AWS_OIDC_CLIENT_SECRET``

`CONTACT Software GmbH`_ will provide every customer with OIDC credentials
during onboarding and the Cloud team can be contacted in case there are any
questions.

Provisioning the project will result in a modified ``python.index_url`` that
allows to install packages from the CodeArtifact registry.

.. code-block:: console
    :caption: Running ``spin provision`` with enabled aws_auth

    spin provision
    spin: mkdir /home/developer/src/my_project/.spin
    spin: mkdir /home/developer/src/my_project/.spin/plugins
    ...
    spin: python -mpip -q --disable-pip-version-check install --index-url https://aws:*******@contact-373369985286.d.codeartifact.eu-central-1.amazonaws.com/pypi/16.0/simple/ -U pip
    ...

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
of csspin. For this case, the configuration tree property ``python.use`` can be
set via command-line, the environment or within ``spinfile.yaml`` to enforce the
usage of the passed interpreter.

.. code-block:: console
    :caption: Using an existing Python interpreter

    spin -p python.use=python provision
    ...
    spin -p python.use=/usr/bin/python <task>

.. _section-label-spin-env:

How to activate the virtual environment provisioned by csspin manually?
#######################################################################

.. Attention:: The activation script presented by ``spin env`` doesn't lead to
               same environment in which ``spin run <command>`` is executed,
               since plugins' hooks are not run through when activating an
               environment by hand! For more information, please refer to
               :ref:`python_virtual_environment`.

Retrieving the path to activate the virtual environment created by the
``python`` plugin is as easy as follows:

.. code-block:: console
    :caption: Retrieving the activate script of the virtual environment provisioned by csspin

    # Unix-style shells:
    spin env
    . /home/developer/src/qs/spin/csspin_python/.spin/venv/bin/activate

    # Powershell 7:
    spin env
    C:\Users\developer\Desktop\csspin\.spin\venv\Scripts\activate.ps1

Activating the virtual environment can be done by sourcing the activate script:

.. code-block:: console
    :caption: Activating the virtual environment provisioned by csspin

    # Unix-style shells:
    $(spin env)

    # Powershell 7:
    & (spin env)

How to modify the behavior of the installation of the current package?
######################################################################

The behavior to install the current package can be modified in two ways.

One is, to include optional dependencies (so called :emphasis:`extras`) of the
current package. This can be done in the ``spinfile.yaml`` like this:

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

How to inject a custom pip configuration within the scope of the environment?
#############################################################################

Adding a site-specific ``pip.conf`` / ``pip.ini`` into the Python virtual
environment can be achieved by leveraging the ``python.pipconf`` property as
follows:

.. code-block:: yaml
    :caption: Using a site-specific configuration for pip

    ...
    python:
        pipconf: |
            [global]
            find-links = {HOME}/.custom_wheel_cache

How to build a wheel?
#####################

Building a wheel for the current package can be done by using the following
command:

.. code-block:: console

    spin python:wheel .

If ``python.build_wheels`` is not specified within the ``spinfile.yaml``, the
same could be achieved with ``spin python:wheel`` (without the path argument).

``python.build_wheel`` allows building multiple wheels with a single ``spin
python:wheel`` command:

.. code-block:: yaml

    # spinfile.yaml
    ...
    python:
        ...
        build_wheels:
            - '{spin.project_root}' # for building the current package
            - cs.componenttest
            - path/to/another/package


``csspin_python.python`` schema reference
#########################################

.. include:: python_schemaref.rst
