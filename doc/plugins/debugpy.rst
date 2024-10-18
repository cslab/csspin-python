.. -*- coding: utf-8 -*-
   Copyright (C) 2024 CONTACT Software GmbH
   All rights reserved.
   https://www.contact-software.com/

.. _spin_python.debugpy:

===================
spin_python.debugpy
===================

The ``spin_python.debugpy`` plugin provisions `debugpy`_ and provides
configuration that can be used in other plugins of spin_python to run debugpy in
order to debug Python code.

This plugin doesn't need to be activated within a ``spinfile.yaml``, it rather
must be used as dependency in other plugins that require debugpy and want to use
the configuration of the debugpy plugin.

How to use the ``spin_python.debugpy`` plugin within other plugins?
###################################################################

To use the ``spin_python.debugpy`` plugin within other plugins, the plugin must
be added as a dependency and can be used as follows:

.. code-block:: python
   :caption: Using the debugpy plugin within another plugin

   from spin import config, task, option, sh

   defaults = config(
       requires=config(
           spin=[
               "spin_python.debugpy",
               "spin_python.python",
           ],
       )
   )


   @task
   def dummy(cfg, debug: option("--debug", is_flag=True), args):
       if debug:
           sh("debugpy", *cfg.debugpy.opts, "-m", "something", args)
       else:
           sh("python", "-m", "something", args)

``spin_python.debugpy`` schema reference
######################################

.. include:: debugpy_schemaref.rst
