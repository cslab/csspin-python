# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the unit tests for csspin_python"""

import re
import sys
from contextlib import nullcontext
from subprocess import CalledProcessError
from unittest import mock

import pytest
from click import Abort

# Mock `csspin.task` away as the import fails otherwise
with mock.patch("csspin.task"):
    from csspin_python.python import (
        _check_venv,
        _configure_pipconf,
        _split_requirement_option,
    )


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


@pytest.mark.parametrize(
    "exists_return, check_output_side_effect, use, "
    "version, expected_result, expect_warn, description",
    [
        # no `use`, version matches prefix -> True
        (
            True,
            [b"Python 3.11.4"],
            None,
            "3.11",
            True,
            False,
            "version matches",
        ),
        # no `use`, version does not match prefix -> False
        (
            True,
            [b"Python 3.10.2"],
            None,
            "3.11",
            False,
            False,
            "version mismatch",
        ),
        # no `use`, empty version string -> False
        (
            True,
            [b"Python "],
            None,
            "3.11",
            False,
            False,
            "empty version output",
        ),
        # `use` set, versions match -> True, no warning
        (
            True,
            [b"Python 3.11.4", b"Python 3.11.4"],
            "/usr/bin/python3.11",
            "3.11",
            True,
            False,
            "use matches venv",
        ),
        # `use` set, versions differ -> True but warning emitted
        (
            True,
            [b"Python 3.11.4", b"Python 3.12.0"],
            "/usr/bin/python3.12",
            "3.11",
            True,
            True,
            "use differs but still healthy",
        ),
        # venv exists but neither version nor use is set -> False
        (
            True,
            [b"Python 3.11.4"],
            None,
            None,
            False,
            False,
            "no version or use configured",
        ),
        # venv exists, use is set but version is not -> True if use matches
        (
            True,
            [b"Python 3.11.4", b"Python 3.11.4"],
            "/usr/bin/python3.11",
            None,
            True,
            False,
            "only use set, matches",
        ),
        # venv exists, use is set but version is not ->
        # True even if use differs (with warning)
        (
            True,
            [b"Python 3.11.4", b"Python 3.12.0"],
            "/usr/bin/python3.12",
            None,
            True,
            True,
            "only use set, differs",
        ),
        # empty string version (edge case)
        (
            True,
            [b"Python 3.11.4"],
            None,
            "",
            False,
            False,
            "empty version string config",
        ),
        # python executable exists but fails to run -> should return False
        (
            True,
            CalledProcessError(1, "python"),
            None,
            "3.11",
            False,
            False,
            "python execution fails",
        ),
        # use is set but points to non-existent executable -> should return False
        (
            True,
            [b"Python 3.11.4", CalledProcessError(1, "python")],
            "/usr/bin/nonexistent",
            "3.11",
            False,
            False,
            "use executable missing",
        ),
    ],
    ids=[
        "version_matches_prefix",
        "version_no_match",
        "empty_version_string",
        "use_versions_match",
        "use_versions_differ_warns",
        "neither_version_nor_use_set",
        "only_use_set_matches",
        "only_use_set_differs",
        "empty_version_config",
        "python_execution_fails",
        "use_executable_missing",
    ],
)
@mock.patch("csspin_python.python.warn")
@mock.patch("csspin_python.python.check_output")
@mock.patch("csspin_python.python.exists")
def test_check_venv(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    mock_exists,
    mock_check_output,
    mock_warn,
    exists_return,
    check_output_side_effect,
    use,
    version,
    expected_result,
    expect_warn,
    description,
):
    """
    Tests the check_venv function for all its cases.
    """
    mock_exists.return_value = exists_return

    # Handle both list of outputs and direct exception
    if isinstance(check_output_side_effect, CalledProcessError):
        mock_check_output.side_effect = check_output_side_effect
    else:
        mock_check_output.side_effect = check_output_side_effect

    cfg = mock.MagicMock()
    cfg.python.python = "venv/bin/python"
    cfg.python.use = use
    cfg.python.version = version

    result = _check_venv(cfg)
    assert result == expected_result, f"Failed: {description}"

    if expect_warn:
        mock_warn.assert_called_once()
        assert "does not match" in mock_warn.call_args[0][0]
    else:
        mock_warn.assert_not_called()
