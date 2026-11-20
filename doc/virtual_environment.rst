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

Running Commands in the Environment
===================================

.. Warning:: Activating the virtual environment by hand is deprecated and will
             be removed in a future release. This includes ``spin env`` and the
             activation scripts that ``spin provision`` patches. Use ``spin run
             <command>`` instead.

To run commands in the Python virtual environment, use ``spin run <command>``,
for example ``spin run zsh`` (or your preferred shell). This approach ensures
that:

* All ``init`` and ``configure`` hooks of provisioned plugins are executed
* Commands obtain the same environment as if executed via ``spin run <command>``
* The environment setup is consistent and reliable

.. Note:: Do not run ``spin`` commands in a shell that ``spin run`` starts. The
          shell already has the environment of the ``spin`` call that started
          it. A nested ``spin`` call can lead to unexpected behavior.

Important Considerations
========================

**Nested Environment Usage**: Running spin from within an activated virtual
environment is discouraged, as this can lead to unexpected behavior.

**Activation Script Integrity**: The activation scripts created during ``spin
provision`` must not be modified manually. This can and will break the setup!
