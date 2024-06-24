# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the integration tests for spin_python"""

import pytest
from spin import backtick, cli


@pytest.fixture(autouse=True)
def cfg():
    """Fixture creating the configuration tree"""
    cli.load_config_tree(None)


def do_test(tmpdir, what, cmd, path="tests/integration/yamls", props=""):
    """Helper to execute spin calls via spin."""
    output = backtick(
        f"spin -p spin.cache={tmpdir} {props} -q -C {path} --env {tmpdir} -f"
        f" {what} --cleanup --provision {cmd}"
    )
    output = output.strip()
    return output


def test_python_use(tmpdir):
    """Ensuring that the python plugin and"""
    output = do_test(
        tmpdir,
        "python.yaml",
        "python --version",
        "tests/integration/testpkg",
        "-p python.use=python",
    )
    assert "Python 3." in output
