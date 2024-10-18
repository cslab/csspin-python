.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_python.radon:

=================
spin_python.radon
=================

The ``spin_python.radon`` plugin provides a way to run the `Radon`_ tool to
measure various code metrics of Python code.

How to setup the ``spin_python.radon`` plugin?
##############################################

For using the ``spin_python.radon`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``spin_python.radon``

    plugin_packages:
        - spin_python
    plugins:
        - spin_python.radon
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

``spin_python.radon`` schema reference
######################################

.. include:: radon_schemaref.rst
