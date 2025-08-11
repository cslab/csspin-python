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

csspin-python documentation
===========================

The ``csspin-python`` plugin-package for spin serves to provide the necessary
plugins and tools for the development and testing of Python-based projects.

It is the most-commonly used plugin-package for spin, as it provides the
``python`` plugin, which creates and manages a virtual environment
in which the necessary Python as well as Node and other dependencies will be
installed.

.. The sources can be found at https://code.contact.de/qs/spin/csspin_python, while
.. the released versions are available at
.. https://pypi.org.

``csspin-python`` requires at least Python 3.9.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   installation.rst
   development.rst
   virtual_environment.rst
   plugins/behave.rst
   plugins/debugpy.rst
   plugins/devpi.rst
   plugins/playwright.rst
   plugins/pytest.rst
   plugins/python.rst
   plugins/radon.rst
