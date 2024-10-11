.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_python.playwright:

======================
spin_python.playwright
======================

The ``spin_python.playwright`` plugin provides a way to run the
`pytest-playwright <https://playwright.dev/>`_ end-to-end testing tool to
execute pre-implemented tests against CONTACT Elements instances by adding the
``playwright`` task to spin's CLI.

How to setup the ``spin_python.playwright`` plugin?
###################################################

For using the ``spin_python.playwright`` plugin, a project's ``spinfile.yaml``
must at least contain the following configuration.

.. code-block:: yaml
    :caption: Minimal configuration of ``spinfile.yaml`` to leverage ``spin_python.playwright``

    plugin_packages:
        - spin_python
    plugins:
        - spin_python.playwright
    python:
        version: "3.11.9"

The provisioning of the required virtual environment as well as the plugins
dependencies can be done via the well-known ``spin provision``-task.

The plugin is now ready to use: ``spin playwright --help``.

How to execute the ``playwright`` task?
#######################################

After provision, the ``playwright`` task can be executed as follows:

.. code-block:: bash
    :caption: Executing playwright

    spin playwright

The ``playwright`` task will execute the tests defined in the
``tests/playwright`` directory of the project. These path can be customized
using the playwright configuration within the ``spinfile.yaml``.


How to run playwright tests against a CONTACT Elements instance?
################################################################

Running playwright tests against a CONTACT Elements instance requires the
existence of it. A typical setup may require a
``spinfile.yaml`` as follows:

.. code-block:: yaml
    :caption: Configuration of ``spinfile.yaml`` to run playwright tests against a CONTACT Elements instance

    plugin_packages:
        - spin_ce
        - spin_frontend
        - spin_python
    plugins:
        - spin_ce:
            - mkinstance # for creating a CE instance
            - ce_services # for starting/stopping CE services
        - spin_frontend.node
        - spin_python.playwright
    python:
        version: '3.11.9'
        index_url: <index url where to retrieve cs.* packages from>
    node:
        version: '18.17.1'

After provisioning the project, the CONTACT Elements instance can be created
and tested using the ``mkinstance`` and ``playwright`` tasks:

.. code-block:: bash
    :caption: Provisioning and running playwright tests against a CONTACT Elements instance

    spin provision
    spin mkinstance
    spin playwright

``spin_python.playwright`` schema reference
###########################################

.. include:: playwright_schemaref.rst
