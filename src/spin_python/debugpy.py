# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com

"""Module providing configurations for the debugpy plugin for cs.spin"""

try:
    from csspin import config
except ImportError:
    from spin import config

defaults = config(
    opts=[
        "--listen localhost:5678",
        "--wait-for-client",
    ],
    requires=config(
        spin=["spin_python.python"],
        python=["debugpy"],
    ),
)
