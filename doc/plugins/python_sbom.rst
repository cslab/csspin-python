.. -*- coding: utf-8 -*-
   Copyright (C) 2026 CONTACT Software GmbH
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

.. _csspin_python.python_sbom:

=========================
csspin_python.python_sbom
=========================

The ``python_sbom`` plugin generates a `CycloneDX`_ Software Bill of Materials
(SBOM) for the Python third-party dependencies of the current project. The
output is written to ``{spin.project_name}.python_sbom.cdx.json`` in the project
root.

.. Attention::
    Only dependencies listed under the ``thirdparty`` extra in the project's
    ``pyproject.toml`` (or ``setup.py``) are included in the SBOM. This design
    choice ensures that only selected third-party packages are considered.

How to set up the ``python_sbom`` plugin?
#########################################

For using the ``python_sbom`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``python_sbom``

    plugin_packages:
        - csspin-python
    plugins:
        - csspin_python.python_sbom
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugin's
dependencies can be done via the well-known ``spin provision`` task.

How to generate a Python SBOM?
##############################

The ``python-sbom`` task is triggered automatically as part of the
``sbom:build`` task group. To invoke it directly:

.. code-block:: console

    spin python-sbom

Defining third-party packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The task relies on a ``thirdparty`` extra defined in the project's
``pyproject.toml`` (or ``setup.py``) to determine which packages
belong in the SBOM. Only the dependencies listed under this extra are included.
The project's own development or test dependencies are intentionally excluded.

.. code-block:: toml
    :caption: ``pyproject.toml`` declaring third-party dependencies for the SBOM

    [project.optional-dependencies]
    thirdparty = [
        "requests>=2.28",
        "pydantic>=2.0",
    ]

If no ``thirdparty`` extra is defined, the task prints a notice and exits
without generating a file.

.. Note::

    ``cyclonedx-bom`` is installed into an isolated temporary virtual
    environment during SBOM generation and does not need to be listed as a
    project dependency.

.. _CycloneDX: https://cyclonedx.org/

``python_sbom`` schema reference
################################

.. include:: python_sbom_schemaref.rst
