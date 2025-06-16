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

.. _csspin_python.devpi:

===================
csspin_python.devpi
===================

The ``devpi`` plugin provides integration with a package index
server using the Python package `devpi`_. The devpi package is useful for those
who need to integrate their project with a package index server for managing and
publishing Python packages.

How to setup the ``devpi`` plugin?
##################################

For using the ``devpi`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``devpi``

    plugin_packages:
        - csspin-python
    plugins:
        - csspin_python.devpi
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

The plugin is now ready to use: ``spin devpi --help``.

How to execute devpi through csspin?
####################################

After provision, the ``devpi`` task can be executed through spin via:

.. code-block:: console
    :caption: Execute the devpi task

    spin devpi

How to upload a wheel to a package server?
##########################################

The ``devpi`` plugin provides a task named "devpi:upload" which builds and
uploads a wheel to a package index.

.. code-block:: console
    :caption: Build and upload a wheel to a package server

    spin -p devpi.user=xyz -p devpi.url=https://pypi.org/simple devpi:upload
    ...
    password for user xyz at https://pypi.org/simple: ************

``devpi`` schema reference
##########################

.. include:: devpi_schemaref.rst
