# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Fixtures for the integration testsuite"""


import pytest


@pytest.fixture(scope="function")
def tmp_dir_per_spinfile(request, tmp_path_factory):
    """
    Fixture to provide a directory for each spinfile being used during
    parametrization. Expects to have the parametrized test function to look like
    this: test_foo[<spinfile_name>:<something>]
    """
    parametrization_start = request.node.name.find("[")
    parametrization = request.node.name[parametrization_start:-1]
    spinfile_name = parametrization[1:].split(":")[0]
    tmp_dir_name = f"{spinfile_name}.d"
    yield tmp_path_factory.getbasetemp() / tmp_dir_name
