# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2026 CONTACT Software GmbH
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

"""Acceptance tests for the python-sbom task."""

import json
import platform
import shutil
import subprocess
import sysconfig
from pathlib import Path

import pytest

HERE = Path(__file__).parent
SPINFILE = str(HERE / "spinfile.yaml")
_PLATFORM_TAG = sysconfig.get_platform().replace("-", "_")
OUTPUT_FILE = HERE / f"dummy-sbom-project.{_PLATFORM_TAG}.python_sbom.cdx.json"


def _execute_command(cmd: list[str]) -> tuple[str, bool]:
    """Execute the given command and return its output and success status."""
    try:
        return (
            subprocess.check_output(cmd, encoding="utf-8", stderr=subprocess.STDOUT),
            True,
        )
    except subprocess.CalledProcessError as ex:
        print(ex.output)
        return ex.output, False


@pytest.fixture(autouse=True)
def cleanup_env():
    """Clean up generated files and spin environment after each test."""
    yield
    shutil.rmtree(HERE / ".spin", ignore_errors=True)
    OUTPUT_FILE.unlink(missing_ok=True)


@pytest.mark.acceptance()
@pytest.mark.parametrize(
    "python_version",
    [
        "3.10.9",
        # >=3.12 dropped distutils from the stdlib, which is why
        # _predict_wheel_filename() must run in an environment with setuptools
        # installed (the project's provisioned venv) rather than spin's bare
        # seed interpreter.
        "3.14.2",
    ],
)
def test_sbom_generates_cdx_json(python_version: str) -> None:
    """Test that python-sbom creates a valid CycloneDX JSON file."""
    base_command = [
        "spin",
        "-C",
        str(HERE),
        "-f",
        SPINFILE,
        "-p",
        f"python.version={python_version}",
    ]

    provision_output, success = _execute_command(base_command + ["provision"])
    assert success, provision_output

    output, success = _execute_command(base_command + ["python-sbom"])
    assert success, output

    assert OUTPUT_FILE.exists(), f"{OUTPUT_FILE.name} was not created"
    content = json.loads(OUTPUT_FILE.read_text(encoding="utf-8"))
    assert content.get("bomFormat") == "CycloneDX"
    components = content.get("components", [])
    component_names = {c.get("name") for c in components}
    assert "packaging" in component_names, "Expected 'packaging' in SBOM components"
    assert (
        "requests" not in component_names
    ), "Dependency 'requests' should not be included as it's not in the 'thirdparty' extra"

    system = platform.system()
    if system == "Windows":
        assert (
            "pypiwin32" in component_names
        ), "Windows-only dep 'pypiwin32' must appear in SBOM on Windows"
        assert (
            "pyinotify" not in component_names
        ), "Linux-only dep 'pyinotify' must not appear in SBOM on Windows"
    elif system == "Linux":
        assert (
            "pyinotify" in component_names
        ), "Linux-only dep 'pyinotify' must appear in SBOM on Linux"
        assert (
            "pypiwin32" not in component_names
        ), "Windows-only dep 'pypiwin32' must not appear in SBOM on Linux"

    primary_ref = "dummy-sbom-project==0.1.0"
    component = content["metadata"]["component"]
    assert component["bom-ref"] == primary_ref
    assert (
        component["author"] == "CONTACT Software GmbH (ptm-team@contact-software.com)"
    )
    assert component["licenses"] == [{"expression": "Apache-2.0"}]
    assert component["purl"] == (
        "pkg:pypi/dummy-sbom-project@0.1.0"
        "?file_name=dummy_sbom_project-0.1.0-py3-none-any.whl"
        r"&repository_url=https:%2F%2Fpackages.contact.de%2Ftools%2Fstable"
    )

    bom_ref_by_name = {c["name"]: c["bom-ref"] for c in components if "bom-ref" in c}
    primary_dep = next(
        (d for d in content.get("dependencies", []) if d["ref"] == primary_ref),
        None,
    )
    assert primary_dep is not None, f"No dependencies entry for {primary_ref}"
    assert bom_ref_by_name["packaging"] in primary_dep["dependsOn"]
    if system == "Linux":
        assert bom_ref_by_name["pyinotify"] in primary_dep["dependsOn"]
    elif system == "Windows":
        assert bom_ref_by_name["pypiwin32"] in primary_dep["dependsOn"]
