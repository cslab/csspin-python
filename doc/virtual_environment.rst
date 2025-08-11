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

.. _python_virtual_environment:

==========================
Python Virtual Environment
==========================

Overview
========

When provisioning the ``csspin_python.python`` plugin or plugins extending the
``SimpleProvisioner`` protocol, a Python virtual environment will be created at
``{python.venv}``. This is the Python environment that spin uses when executing
subcommands like ``spin pytest`` and ``spin run <something>``.

Environment Activation
======================

Basic Activation
----------------

The virtual environment can be activated as described in :ref:`spin env
<section-label-spin-env>`. This allows executing non-spin commands and
executables like ``foo.exe`` within the environment without the need for calling
``spin run foo.exe``.

.. Warning:: When manually activating the environment, ``configure`` and
             ``init`` hooks of provisioned spin plugins are *not* executed. This
             leads to a slightly different environment than the one used when
             running ``spin run``.

Recommended Approach
--------------------

Instead of manually activating the Python virtual environment, we recommend
using ``spin run zsh`` (or your preferred shell). This approach ensures that:

* All ``init`` and ``configure`` hooks of provisioned plugins are executed
* Commands obtain the same environment as if executed via ``spin run <command>``
* The environment setup is consistent and reliable

Important Considerations
========================

**Nested Environment Usage**: Running spin from within an activated virtual
environment is discouraged, as this can lead to unexpected behavior.

**Activation Script Integrity**: The activation scripts created during ``spin
provision`` must not be modified manually. This can and will break the setup!
