.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

==================
Plugin development
==================

This section addresses the development of and with the ``spin_python``
plugin-package.

How does a plugin define Python dependencies?
#############################################

A plugin that depends on ``spin_python.python`` can depend on other Python
packages. These plugin-specific dependencies can be defined using
``requires.python``.

Dependencies are installed while executing ``spin provision`` and can then be
used within any function of the plugin.

.. code-block:: python
    :caption: Declaring Python dependencies of a dummy plugin

    from spin import config


    defaults = config(
        requires=config(
            spin=["spin_python.python"],
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

cs.spin's API already provides the ``spin.setenv`` function that enables setting
environment variables for the current process.

In combination with the ``spin_python.python`` plugin, these environment
variables are written into the Python virtual environment in case the plugin
depends on ``spin_python.python`` and ``spin.setenv`` is called during
``configure(cfg)`` or ``provision(cfg)`` of the current plugin.

.. code-block:: python
    :caption: Writing environment variables into the Python virtual environment

    from spin import config, setenv

    defaults = config(spin=["spin_python.python"])


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

The ``spin_python.python`` plugin implements a ``ProvisionerProtocol`` interface
that forms the base of the default provisioner ``SimpleProvisioner``, which is
using the Python package manager `pip <https://pip.pypa.io/en/stable/>`_ to
install and manage Python dependencies.
