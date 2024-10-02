.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_python.devpi:

=================
spin_python.devpi
=================

The ``spin_python.devpi`` plugin provides integration with a package index
server using the Python package `devpi <https://github.com/devpi/devpi>`_. The
devpi package is useful for those who need to integrate their project with
a package index server for managing and publishing Python packages.

How to setup the ``spin_python.devpi`` plugin?
###############################################

For using the ``spin_python.devpi`` plugin, a project's ``spinfile.yaml`` must
at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``spin_python.devpi``

    plugin-packages:
        - spin_python
    plugins:
        - spin_python.devpi
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

The plugin is now ready to use: ``spin devpi --help``.

How to execute devpi through cs.spin?
#####################################

After provision, the ``devpi`` task can be executed through spin via:

.. code-block:: console
    :caption: Execute the devpi task

    spin devpi

How to upload a wheel to a package server?
##########################################

The ``spin_python.devpi`` plugin provides a task named "devpi:upload" which builds and
uploads a wheel to a package index.

.. code-block:: console
    :caption: Build and upload a wheel to a package server

    spin -p devpi.user=xyz -p devpi.url=https://pypi.org/simple devpi:upload
    ...
    password for user xyz at https://pypi.org/simple: ************

``spin_python.devpi`` schema reference
#######################################

.. include:: devpi_schemaref.rst
