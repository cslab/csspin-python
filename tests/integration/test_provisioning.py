# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the integration tests for spin_python"""

import functools
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

PYTHON_EXISTS = shutil.which("python")
PYTHON_SKIP_MARK = pytest.mark.skipif(not PYTHON_EXISTS, reason="python not installed.")


def run_command_in_env(cmd, spin_cmd):
    """Helper function to run a subprocess in a provisioned spin environment."""
    command = spin_cmd.copy()
    command.extend(cmd)
    print(subprocess.list2cmdline(command))
    return subprocess.check_output(command, encoding="utf-8").strip()


@functools.cache
def provision_env(spinfile, tmp_path, cwd="tests/integration"):
    """
    Helper function to provision a spin environment based on the spinfile provided by
    spinfile.

    Returns a tuple (cache, cmd) where `cache` is the location of the
    provisioned environments cache-dir and `cmd` is a commandline as a list to
    build commands to run subprocesses inside the provisioned env.
    """
    if spinfile == "python_use.yaml" and not PYTHON_EXISTS:
        pytest.skip("python not available")

    spinfile_path = os.path.join("tests", "integration", "yamls", spinfile)
    cache = tmp_path / ".cache"
    cache.mkdir(parents=True, exist_ok=True)

    base_cmd = [
        "spin",
        "-q",
        "-p",
        f"spin.cache={cache}",
        "-C",
        cwd,
        "--env",
        str(tmp_path),
        "-f",
        spinfile_path,
    ]
    cmd = base_cmd + ["--provision"]
    print(subprocess.list2cmdline(cmd))
    try:
        subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        print(ex.stdout)
    return (tmp_path, base_cmd)


TESTCASES = (
    pytest.param(  # pylint: disable=no-member
        "python_version.yaml",
        "python",
        "3.9",
        id="python_version.yaml",
    ),
    pytest.param(  # pylint: disable=no-member
        "python_use.yaml",
        "python",
        (
            None
            if not PYTHON_EXISTS
            else subprocess.check_output(
                ["python", "--version"],
                encoding="utf-8",
            ).strip()
        ),
        id="python_use.yaml",
        marks=PYTHON_SKIP_MARK,
    ),
    pytest.param(  # pylint: disable=no-member
        "behave.yaml",
        "behave",
        "",
        id="behave.yaml",
        marks=PYTHON_SKIP_MARK,
    ),
    pytest.param(  # pylint: disable=no-member
        "devpi.yaml",
        "devpi",
        "",
        id="devpi.yaml",
        marks=PYTHON_SKIP_MARK,
    ),
    pytest.param(  # pylint: disable=no-member
        "pytest.yaml",
        "pytest",
        "",
        id="pytest.yaml",
        marks=PYTHON_SKIP_MARK,
    ),
    pytest.param(  # pylint: disable=no-member
        "radon.yaml",
        "radon",
        "",
        id="radon.yaml",
        marks=PYTHON_SKIP_MARK,
    ),
    pytest.param(  # pylint: disable=no-member
        "playwright.yaml",
        "playwright",
        "",
        id="playwright.yaml",
        marks=PYTHON_SKIP_MARK,
    ),
)


@pytest.mark.integration()
@pytest.mark.parametrize("spinfile, tool, _version", TESTCASES)
def test_tool_path(spinfile, tool, _version, tmp_dir_per_spinfile):
    """
    Check whether the expected tools with the correct version is available in
    the provisioned env.
    """
    tmp_path, env_cmd = provision_env(spinfile, tmp_dir_per_spinfile)

    if sys.platform == "win32":
        cmd = [
            "run",
            "powershell",
            "-C",
            f"(get-command {tool}).path",
        ]
    else:
        cmd = ["run", "which", tool]
    tool_path = Path(run_command_in_env(cmd, env_cmd))
    assert tmp_path in tool_path.parents


@pytest.mark.integration()
@pytest.mark.parametrize("spinfile, tool, version", TESTCASES)
def test_tool_available(spinfile, tool, version, tmp_dir_per_spinfile):
    """
    Check whether the expected tools with the correct version is available in
    the provisioned env - if no version passed, just checking for --help.
    """
    _, env_cmd = provision_env(spinfile, tmp_dir_per_spinfile)

    if version:
        assert version in run_command_in_env(["run", tool, "--version"], env_cmd)
    else:
        run_command_in_env(["run", tool, "--help"], env_cmd)


@pytest.mark.integration()
def test_devpackage_provision(tmp_path):
    """
    Ensure that a project can be provisioned using the python plugin, along with
    it's devpackage configuration.
    """
    if not PYTHON_EXISTS:
        pytest.skip("python not available")

    base_cmd = [
        "spin",
        "-q",
        "-p",
        f"spin.cache={tmp_path}",
        "-C",
        "tests/integration/fixtures/testpkg",
        "--env",
        str(tmp_path),
    ]

    cmd = base_cmd + ["--provision"]
    print(subprocess.list2cmdline(cmd))
    try:
        subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        print(ex.stdout)

    pip_list = run_command_in_env(["run", "pip", "list"], base_cmd)
    assert "testpkg" in pip_list
    assert "devpkg" in pip_list
