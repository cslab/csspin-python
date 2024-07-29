# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Fixtures for the integration testsuite"""

import os

import pytest


@pytest.fixture(scope="session", autouse=True)
def disable_global_yaml():
    "Fixture to let spin ignore the global yaml."
    if not os.environ.get("CI"):
        os.environ["SPIN_DISABLE_GLOBAL_YAML"] = "True"
