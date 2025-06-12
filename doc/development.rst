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

==================
Plugin development
==================

This section addresses the development of and with the ``csspin_python``
plugin-package.

How does a plugin define Python dependencies?
#############################################

A plugin that depends on ``python`` can depend on other Python
packages. These plugin-specific dependencies can be defined using
``requires.python``.

Dependencies are installed while executing ``spin provision`` and can then be
used within any function of the plugin.

.. code-block:: python
    :caption: Declaring Python dependencies of a dummy plugin

    from csspin import config


    defaults = config(
        requires=config(
            spin=["csspin_python.python"],
            python=["requests"],
        ),
    )


    def configure():
        """Configuring the dummy plugin"""
        import requests

        ...


    def dummy():
        """This is a dummy plugin"""
        ...

How to write environment variables into the Python virtual environment?
#######################################################################

spin's API already provides the ``csspin.setenv`` function that enables setting
environment variables for the current process.

In combination with the ``python`` plugin, these environment
variables are written into the Python virtual environment in case the plugin
depends on ``python`` and ``csspin.setenv`` is called during
``configure(cfg)`` or ``provision(cfg)`` of the current plugin.

.. code-block:: python
    :caption: Writing environment variables into the Python virtual environment

    from csspin import config, setenv

    defaults = config(spin=["csspin_python.python"])


    def configure(cfg):
        setenv(FOO="bar")


    def provision(cfg):
        setenv(PIPAPO="...")
        ...


    ...

After provision of a project using the plugin module above, the environment
variable ``FOO`` is available within the Python virtual environment, i.e. also
when activating the virtual environment manually. This is useful for such
environment variables that are required by plugins during runtime and don't
change when working with the same environment.

What is the use of ``ProvisionerProtocol``?
###########################################

Python packages are installed through a provisioner, which is responsible for
the dependency management strategy.

The ``python`` plugin implements a ``ProvisionerProtocol`` interface
that forms the base of the default provisioner ``SimpleProvisioner``, which is
using the Python package manager `pip <https://pip.pypa.io/en/stable/>`_ to
install and manage Python dependencies.
