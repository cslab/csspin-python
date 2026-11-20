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

This section addresses the development of and with the ``csspin-python``
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

How does a plugin set environment variables?
############################################

A plugin sets the environment variables it needs in its ``init`` hook, with the
``csspin.setenv`` function. spin runs the ``init`` hook on every ``spin``
call, so the variables are available to every command that spin starts.

``spin provision`` runs no ``init`` hook. A plugin that needs a variable during
provision also sets it in ``provision``. The ``csspin-java`` plugin is a model
for this pattern. For details, see `csspin's plugin guide
<https://csspin.readthedocs.io/en/stable/howtoplugins.html>`_.

.. code-block:: python
    :caption: Setting environment variables in a plugin

    from csspin import config, setenv

    defaults = config(requires=config(spin=["csspin_python.python"]))


    def init(cfg):
        setenv(FOO="bar")


    def provision(cfg):
        # "spin provision" runs no "init" hook.
        setenv(FOO="bar")
        ...

.. note::
    The ``python`` plugin writes the variables that ``setenv`` records into the
    activation scripts of the virtual environment. This patching is deprecated.
    See :ref:`python_virtual_environment`.

What is the use of ``ProvisionerProtocol``?
###########################################

Python packages are installed through a provisioner, which is responsible for
the dependency management strategy.

The ``python`` plugin implements a ``ProvisionerProtocol`` interface
that forms the base of the default provisioner ``SimpleProvisioner``, which is
using the Python package manager `pip <https://pip.pypa.io/en/stable/>`_ to
install and manage Python dependencies.
