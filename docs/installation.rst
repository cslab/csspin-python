.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

======================
Installation and setup
======================

cs.spin must be installed beforehand, this can be done as documented at
http://qs.pages.contact.de/spin/cs.spin/installation.html.

For leveraging plugins from within the ``spin_python`` plugin-package for
``cs.spin``,  ``spin_python`` must be added to the list of plugin-packages
within a project's ``spinfile.yaml``.

.. code-block:: yaml
    :caption: Example: ``spinfile.yaml`` setup to enable the pytest and python plugins

    minimum-spin: "0.2"
    plugin-packages:
        - spin_python
    plugins:
        - spin_python:
            - python
            - pytest
    python:
        version: "3.11.9"

After the configuration is done, the plugin-package can be provisioned by
executing the following command within the project's directory:

.. code-block:: console

    spin provision

The plugins defined in the plugins section of the ``spinfile.yaml`` can now be
used:

.. code-block:: console

    spin pytest --help
