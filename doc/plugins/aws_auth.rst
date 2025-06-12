.. -*- coding: utf-8 -*-
   Copyright (C) 2025 CONTACT Software GmbH
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

.. _csspin_python.aws_auth:

======================
csspin_python.aws_auth
======================

The ``aws_auth`` plugin provides a way to configure the
``index_url`` property of the ``python`` plugin, so that packages are being
installed from an AWS CodeArtifact instance.

How to setup the ``aws_auth`` plugin?
#####################################

To use the ``aws_auth`` plugin, a project's ``spinfile.yaml`` must at
least contain the following configuration.

.. code-block:: yaml
    :caption: Basic configuration of ``spinfile.yaml`` to leverage ``aws_auth``

    plugin_packages:
        - csspin_python
    plugins:
        - csspin_python.aws_auth
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

How does it work?
#################

The ``aws_auth`` plugin retrieves an **AWS CodeArtifact key** and embeds it into
a URL, which is then used to access the AWS codeartifact pip repository.

The plugin executes **before provisioning**, during the ``configure`` stage.
This ensures that CodeArtifact is available throughout the provisioning process.

``aws_auth`` updates the repository URL in ``.spin/venv/pip.conf`` to ensure
that calling pip within the spin environment:

    spin run pip ...

always uses the latest authentication key.

Unlike ``aws_auth``, the ``python`` plugin updates ``pip.conf`` only
during provisioning, whereas ``aws_auth`` additionally ensures that ``pip.conf``
always contains the latest AWS CodeArtifact credentials on every run.

``aws_auth`` schema reference
#############################

.. include:: aws_auth_schemaref.rst
