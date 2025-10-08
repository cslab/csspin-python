# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the unit tests for csspin_python"""

import re
import sys
from contextlib import nullcontext
from unittest import mock

import pytest
from click import Abort

# Mock `csspin.task` away as the import fails otherwise
with mock.patch("csspin.task"):
    from csspin_python.python import _configure_pipconf, _split_requirement_option


@pytest.mark.parametrize(
    "pipconf,expected_index",
    (
        ("[global]\ntimeout=10", "https://pypi.org/simple"),
        ("[install]\ntimeout=10", "https://pypi.org/simple"),
        (
            "[global]\ntimeout=10\nindex_url=https://example.com/simple",
            "https://example.com/simple",
        ),
        (
            "[global]\ntimeout=10\nindex-url=https://example.com/simple2",
            "https://example.com/simple2",
        ),
    ),
)
def test__configure_pipconf(tmp_path, pipconf, expected_index):
    """
    Test whether _configure_pipconf handles the index_url properly.
    """
    config_file = (
        tmp_path / "pip.conf" if sys.platform != "win32" else tmp_path / "pip.ini"
    )
    config_file.touch()
    cfg_mock = mock.MagicMock()
    cfg_mock.python.index_url = "https://pypi.org/simple"
    cfg_mock.python.pipconf = pipconf
    cfg_mock.python.venv = tmp_path

    _configure_pipconf(cfg_mock)

    with open(config_file, encoding="utf-8") as fd:
        content = fd.read()
        assert re.search(r"index[-_]url", content)
        for line in content.splitlines():
            if re.match(r"^index[-_]url", line):
                assert expected_index in line


@pytest.mark.parametrize(
    "requirement, expected_filename, context",
    (
        ("-r requirements.txt", "requirements.txt", nullcontext()),
        ("-r=foo.txt", "foo.txt", nullcontext()),
        ("-r    bar.txt", "bar.txt", nullcontext()),
        ("-rbaz.txt", "baz.txt", nullcontext()),
        ("--requirement requirements.txt", "requirements.txt", nullcontext()),
        ("--requirement=foo.txt", "foo.txt", nullcontext()),
        ("--requirement    bar.txt", "bar.txt", nullcontext()),
        ("-c constraint.txt", "constraint.txt", nullcontext()),
        ("-c=foo.txt", "foo.txt", nullcontext()),
        ("-c    bar.txt", "bar.txt", nullcontext()),
        ("-cbaz.txt", "baz.txt", nullcontext()),
        ("--constraint constraint.txt", "constraint.txt", nullcontext()),
        ("--constraint=foo.txt", "foo.txt", nullcontext()),
        ("--constraint    bar.txt", "bar.txt", nullcontext()),
        ("--requirementrequirements.txt", "requirements.txt", pytest.raises(Abort)),
        ("--constraint", "constraint.txt", pytest.raises(Abort)),
    ),
)
def test__split_requirement_option(tmp_path, requirement, expected_filename, context):
    """
    Test whether _split_requirement_option works correctly.
    """
    expected_file = tmp_path / expected_filename
    expected_file.touch()
    with context:
        assert (
            _split_requirement_option(requirement, tmp_path)
            == tmp_path / expected_filename
        )
