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

.. _csspin_python.uv_provisioner:

============================
csspin_python.uv_provisioner
============================

The ``uv_provisioner`` plugin can be used to change the way the
:ref:`csspin_python.python` creates the virtual environment and installs the
Python packages into it. To do so, the plugin uses `uv`_.

How to setup the ``uv_provisioner`` plugin?
###########################################

For using the ``uv_provisioner`` plugin, a project's ``spinfile.yaml`` must at
least contain the following configuration. Note, that the ``uv`` extra of the
csspin-python plugin-package must be installed for the plugin to work.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage the ``uv_provisioner``

    plugin_packages:
        - csspin-python[uv]
    plugins:
        - csspin_python:
            - uv_provisioner
    python:
        version: "3.11.9"
    uv_provisioner:
        enabled: true

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

Things to watch out for when using the ``uv_provisioner`` plugin
################################################################

Index URL
---------

When using the ``uv_provisioner`` plugin you must make sure to set
``python.index_url`` so that it points to a simple index.

Windows Defender
----------------

Windows Defender is quite aggressive about ``uv``, which comes to show
especially during ``spin provision`` when the ``uv_provisioner`` is installing
the Python packages.

To speed this up you can exclude the following directories from Windows
Defender. Please note that this comes with additional security risks. Please
also consult `the documentation from Microsoft
<https://learn.microsoft.com/en-us/defender-endpoint/common-exclusion-mistakes-microsoft-defender-antivirus>`__
in the matter, since excluding temporary directories is considered unsafe:

- ``%LOCALAPPDATA%\uv\cache``
- ``%TEMP%``
- ``%TMP%``
- ``%TMPDIR%``

Installations from VCS
----------------------

The ``uv_provisioner`` considers Python packages defined in
``python.requirements``. Unlike ``pip``, ``uv pip`` does not support installing
from Git repositories that require Git LFS to checkout the sources out of
the box, e.g. from ``git+https://code.contact.de/po/cs.projects.git@master``.
Users need to enable this by setting ``UV_GIT_LFS=1`` in their environment.

``csspin_python.uv_provisioner`` schema reference
#################################################

.. include:: uv_provisioner_schemaref.rst
