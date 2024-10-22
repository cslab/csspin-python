.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

spin_python documentation
=========================

The ``spin_python`` plugin-package for cs.spin serves to provide the necessary
plugins and tools for the development and testing of Python-based projects.

It is the most-commonly used plugin-package for cs.spin, as it provides the
``spin_python.python`` plugin, which creates and manages a virtual environment
in which the necessary Python as well as Node and other dependencies will be
installed.

The sources can be found at https://code.contact.de/qs/spin/spin_python, while
the released versions are available at
https://packages.contact.de/tools/misc/spin-python.

``spin_python`` requires at least Python 3.9.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation.rst
   development.rst
   plugins/behave.rst
   plugins/debugpy.rst
   plugins/devpi.rst
   plugins/playwright.rst
   plugins/pytest.rst
   plugins/python.rst
   plugins/radon.rst
