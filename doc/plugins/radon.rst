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

.. _csspin_python.radon:

====================
csspin_python.radon
====================

The ``radon`` plugin provides a way to run the `Radon`_ tool to
measure various code metrics of Python code.

How to setup the ``radon`` plugin?
##################################

For using the ``radon`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``radon``

    plugin_packages:
        - csspin_python
    plugins:
        - csspin_python.radon
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

The plugin is now ready to use: ``spin radon --help``.

How to execute the ``radon`` task?
##################################

After provision, the ``radon`` task can be executed as follows:

.. code-block:: console
    :caption: Executing radon

    spin radon

``radon`` schema reference
##########################

.. include:: radon_schemaref.rst
