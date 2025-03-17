.. -*- coding: utf-8 -*-
   Copyright (C) 2025 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_python.aws_auth:

====================
spin_python.aws_auth
====================

The ``spin_python.aws_auth`` plugin provides a way to configure the
``index_url`` property of the ``spin_python.python`` plugin, so that packages are being
installed from an AWS CodeArtifact instance.

How to setup the ``spin_python.aws_auth`` plugin?
#################################################

To use the ``spin_python.aws_auth`` plugin, a project's ``spinfile.yaml`` must at
least contain the following configuration.

.. code-block:: yaml
    :caption: Basic configuration of ``spinfile.yaml`` to leverage ``spin_python.aws_auth``

    plugin_packages:
        - spin_python
    plugins:
        - spin_python.aws_auth
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

How does it work?
#################

The `aws_auth` plugin retrieves an **AWS CodeArtifact key** and embeds it into a URL, which is then used to access the AWS codeartifact pip repository.

The plugin executes **before provisioning**, during the `configure` stage. This ensures
that CodeArtifact is available throughout the provisioning process.

`aws_auth` updates the repository URL in ``.spin/venv/pip.conf`` to ensure that calling pip within Spin's shell::

    spin run pip ...

always uses the latest authentication key.

Unlike `aws_auth`, the `spin_python.python` plugin updates ``pip.conf`` only
during provisioning, whereas `aws_auth` additionally ensures that `pip.conf`
always contains the latest AWS CodeArtifact credentials on every run.

``spin_python.aws_auth`` schema reference
#########################################

.. include:: aws_auth_schemaref.rst
