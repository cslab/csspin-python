# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# https://www.contact-software.com/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Acceptance tests for Python.constraints handling."""

import shutil
import subprocess
from pathlib import Path

import pytest

SPINFILE = str(Path(__file__).parent / "spinfile.yaml")


def _execute_command(cmd: list[str]) -> tuple[str, bool]:
    """Execute the given command and return its output and success status."""
    try:
        return (
            subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.STDOUT),
            True,
        )
    except subprocess.CalledProcessError as ex:
        print(ex.stdout)
        return ex.stdout, False


@pytest.fixture
def cleanup_env():
    """Fixture to clean up any created .spin directories after the test."""
    yield
    shutil.rmtree(Path(__file__).parent / ".spin", ignore_errors=True)


@pytest.mark.parametrize(
    "extra_properties,install_command",
    (
        ([], ["pip", "install"]),
        (["-p", "uv_provisioner.enabled=true"], ["uv", "pip", "install"]),
    ),
    ids=("SimpleProvisioner", "UVProvisioner"),
)
def test_constraints(
    extra_properties: list[str],
    install_command: list[str],  # pylint: disable=unused-argument
    cleanup_env,  # pylint: disable=unused-argument,redefined-outer-name
) -> None:
    """Test that Python constraints are handled correctly for various cases."""
    base_command = [
        "spin",
        "-C",
        Path(__file__).parent,
        "-f",
        SPINFILE,
        *extra_properties,
    ]

    # Check constraints are applied during provisioning
    output, success = _execute_command(base_command + ["provision"])
    if not success:
        raise AssertionError(output)

    output, success = _execute_command(
        base_command
        + [
            "-q",
            "run",
            "python",
            "-c",
            "from importlib.metadata import version; print(version('psutil'))",
        ]
    )
    if not success:
        raise AssertionError(output)
    assert output.strip()[-5:] == "7.1.0", output
