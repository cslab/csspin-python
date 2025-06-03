# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the unit tests for spin_python"""

import importlib.util
import re
from unittest import mock

import pytest

# FIXME: remove this once csspin is released and used by this project
if importlib.util.find_spec("spin") is not None:
    # Mock `spin.task` away as the import fails otherwise
    with mock.patch("spin.task"):
        from spin_python.python import _create_pipconf
else:
    # If spin is not found, try with csspin
    # Mock `csspin.task` away as the import fails otherwise
    with mock.patch("csspin.task"):
        from spin_python.python import _create_pipconf


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
def test__create_pipconf(tmp_path, pipconf, expected_index):
    """
    Test whether _create_pip_conf handles the index_url properly.
    """
    config_file = tmp_path / "pip.conf"
    config_file.touch()
    cfg_mock = mock.MagicMock()
    cfg_mock.python.index_url = "https://pypi.org/simple"
    cfg_mock.python.pipconf = pipconf

    _create_pipconf(cfg_mock, config_file)

    with open(config_file, encoding="utf-8") as fd:
        content = fd.read()
        assert re.search(r"index[-_]url", content)
        for line in content.splitlines():
            if re.match(r"^index[-_]url", line):
                assert expected_index in line
