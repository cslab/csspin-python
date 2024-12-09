# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/
#
# pylint: skip-file

import sys

from spin import setenv


def provision(cfg):
    if sys.platform == "win32":
        setenv(FOO="c:\\tmp\\foobar;{FOO}")
    else:
        setenv(FOO="/tmp/foobar:{FOO}")

    setenv(BAR=None)
