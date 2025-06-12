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

.. _csspin_python.debugpy:

=====================
csspin_python.debugpy
=====================

The ``debugpy`` plugin provisions `debugpy`_ and provides configuration that can
be used in other plugins of csspin_python to run debugpy in order to debug
Python code.

This plugin doesn't need to be activated within a ``spinfile.yaml``, it rather
must be used as dependency in other plugins that require debugpy and want to use
the configuration of the debugpy plugin.

How to use the ``debugpy`` plugin within other plugins?
#######################################################

To use the ``debugpy`` plugin within other plugins, the plugin must
be added as a dependency and can be used as follows:

.. code-block:: python
   :caption: Using the debugpy plugin within another plugin

   from spin import config, task, option, sh

   defaults = config(
       requires=config(
           spin=[
               "csspin_python.debugpy",
               "csspin_python.python",
           ],
       )
   )


   @task
   def dummy(cfg, debug: option("--debug", is_flag=True), args):
       if debug:
           sh("debugpy", *cfg.debugpy.opts, "-m", "something", args)
       else:
           sh("python", "-m", "something", args)

``debugpy`` schema reference
############################

.. include:: debugpy_schemaref.rst
