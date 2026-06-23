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

"""Module implementing the python_sbom plugin for csspin"""

import email.utils
import json
import sys
import sysconfig
from importlib.metadata import metadata as _pkg_metadata
from importlib.metadata import version as _pkg_version
from subprocess import DEVNULL, PIPE
from tempfile import TemporaryDirectory

from csspin import (
    Verbosity,
    backtick,
    config,
    die,
    exists,
    info,
    memoizer,
    rmtree,
    sh,
    task,
)
from csspin.tree import ConfigTree
from packaging.requirements import Requirement
from path import Path

defaults = config(
    cyclonedx_bom_version="7.3.0",
    project_paths=["{spin.project_root}"],
    requires=config(spin=["csspin_python.python"]),
)


@task("python-sbom", when="sbom:build")
def sbom(cfg: ConfigTree) -> None:
    """
    Create the SBOMs for Python projects defined in via
    'python_sbom.project_paths'.

    This task assumes that the current package defines its dependencies that
    are to be included in the SBOM via the "thirdparty" extra.

    If there is no such extra, the SBOM generation is skipped.
    """
    from csspin_python.python import get_project_metadata

    stderr = PIPE if cfg.verbosity > Verbosity.NORMAL else DEVNULL
    for project_path in cfg.python_sbom.project_paths:
        if not exists(project_path):
            die(f"Project path '{project_path}' does not exist.")

        project_path = Path(project_path).absolute()
        metadata = get_project_metadata(project_path, cfg.python.index_url)
        third_party_deps = _collect_thirdparty_deps(
            metadata.get("requires_dist", set()), python_version=cfg.python.version
        )
        sbom_json = json.loads(_run_cyclonedx(cfg, third_party_deps, stderr))
        _enrich_sbom(sbom_json, metadata, third_party_deps)
        _write_sbom(cfg, sbom_json, metadata.get("name"))


def cleanup(cfg: ConfigTree) -> None:
    """Get rid of all generated .cdx.json files and the cyclonedx-bom venv."""
    for cdx_file in cfg.spin.project_root.glob("*.python_sbom.cdx.json"):
        rmtree(cdx_file)
    rmtree(cfg.spin.project_root / ".spin" / "venv_csspin_python__python_sbom")


# ---- Internals ---------------------------------------------------------------


def _ensure_cyclonedx_venv(cfg: ConfigTree, binary_dir: str, quiet: str | None) -> Path:
    """Return the cyclonedx-bom interpreter path, (re)creating the venv if needed.

    We install cyclonedx-bom into a persistent venv since defining it as a
    dependency of csspin-python itself doesn't work at this moment.
    See https://github.com/CycloneDX/cyclonedx-python/issues/1045
    """
    venv_cdx = cfg.spin.project_root / ".spin" / "venv_csspin_python__python_sbom"
    interpreter_cdx = venv_cdx / binary_dir / "python" + cfg.platform.exe

    requested_version = cfg.python_sbom.cyclonedx_bom_version
    memo_key = f"cyclonedx-bom=={requested_version}"
    memo_file = venv_cdx / "csspin_python_sbom.memo"

    if venv_cdx.exists():
        with memoizer(memo_file) as memo:
            if memo.check(memo_key):
                info(
                    f"Reusing existing cyclonedx-bom {requested_version} from {venv_cdx}"
                )
                return interpreter_cdx
        info(
            f"cyclonedx-bom version mismatch (wanted={requested_version}), "
            f"recreating {venv_cdx}"
        )
        rmtree(venv_cdx)

    sh(cfg.python.interpreter, "-m", "venv", venv_cdx)
    sh(
        interpreter_cdx,
        "-m",
        "pip",
        quiet,
        "--disable-pip-version-check",
        "install",
        "--index-url",
        cfg.python.index_url,
        "cyclonedx-bom==" + requested_version,
    )
    with memoizer(memo_file) as memo:
        memo.add(memo_key)
    return interpreter_cdx


def _run_cyclonedx(cfg: ConfigTree, third_party_deps: set[str], stderr: int) -> str:
    """
    Install third-party deps into a temp venv and return the CycloneDX JSON.
    """

    binary_dir = "Scripts" if sys.platform == "win32" else "bin"
    quiet = None if cfg.verbosity > Verbosity.NORMAL else "-q"
    interpreter_cdx = _ensure_cyclonedx_venv(cfg, binary_dir, quiet)

    with TemporaryDirectory() as tmp_dir:
        venv = Path(tmp_dir) / "venv"
        interpreter = venv / binary_dir / "python" + cfg.platform.exe
        sh(cfg.python.interpreter, "-m", "venv", venv)
        if third_party_deps:
            sh(
                interpreter,
                "-m",
                "pip",
                quiet,
                "install",
                "--index-url",
                cfg.python.index_url,
                *[
                    f"--constraint={constraint}"
                    for constraint in cfg.python.constraints
                ],
                *third_party_deps,
                stderr=stderr,
            )
        sh(interpreter, "-m", "pip", quiet, "uninstall", "-y", "pip")
        return backtick(interpreter_cdx, "-m", "cyclonedx_py", "environment", venv, stderr=stderr)  # type: ignore[no-any-return] # noqa: E501


def _write_sbom(cfg: ConfigTree, sbom_json: dict, project_name: str) -> None:
    """Write the CycloneDX JSON document to the output file."""
    platform_tag = sysconfig.get_platform().replace("-", "_")
    output_file = cfg.spin.project_root / (
        f"{project_name}.{platform_tag}.python_sbom.cdx.json"
    )
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(sbom_json, f, indent=2, sort_keys=True)
    info(f"Generated Python SBOM successfully ({output_file})")


def _parse_authors(author_name: str, author_email: str) -> str:
    """Parse RFC 2822 Author-email metadata into 'name (email)' format."""
    if not author_email:
        die("Project metadata has no Author-email field.")
        return ""

    entries = email.utils.getaddresses([author_email])

    if len(entries) == 1 and not entries[0][0] and author_name:
        entries = [(author_name, entries[0][1])]

    for name, addr in entries:
        if not name:
            die(f"Author entry '{addr}' has no name; all authors require a name.")
            return ""
        if not addr:
            die(f"Author entry '{name}' has no email; all authors require an email.")
            return ""

    return ", ".join(f"{name} ({addr})" for name, addr in entries)


def _build_primary_component(metadata: dict) -> tuple[dict, str]:
    """Build the CycloneDX primary component dict and its bom-ref from project metadata."""
    if not (name := metadata.get("name")):
        die("Project metadata is missing 'name'.")
    if not (version := metadata.get("version")):
        die("Project metadata is missing 'version'.")
    if not (license_id := metadata.get("license")):
        die("Project metadata is missing 'license'.")

    authors = _parse_authors(
        author_name=metadata.get("author", "").strip(),
        author_email=metadata.get("author_email", "").strip(),
    )
    primary_ref = f"{name}=={version}"
    component = {
        "author": authors,
        "bom-ref": primary_ref,
        "licenses": [{"expression": license_id}],
        "name": name,
        "type": "application",
        "version": version,
    }
    return component, primary_ref


def _enrich_sbom(
    sbom_json: dict,
    metadata: dict,
    third_party_deps: set[str],
) -> None:
    """Add the primary component and its dependency entry to the CycloneDX document."""
    component, primary_ref = _build_primary_component(metadata)
    existing_metadata = sbom_json.get("metadata", {})
    existing_tools = existing_metadata.get("tools", {})
    existing_tool_components = (
        existing_tools
        if isinstance(existing_tools, list)
        else existing_tools.get("components", [])
    )
    sbom_json["metadata"] = {
        **existing_metadata,
        "component": component,
        "tools": {
            "components": existing_tool_components
            + [
                {
                    "description": "Python SBOM plugin for csspin",
                    "licenses": [
                        {
                            "expression": _pkg_metadata("csspin-python")[
                                "License-Expression"
                            ]
                        }
                    ],
                    "name": "csspin-python",
                    "supplier": {
                        "name": "CONTACT Software GmbH",
                        "url": [
                            "https://www.contact-software.com/",
                            "https://pypi.org/project/csspin-python/",
                        ],
                    },
                    "type": "application",
                    "version": _pkg_version("csspin-python"),
                }
            ]
        },
    }
    direct_dep_names = {Requirement(dep).name.lower() for dep in third_party_deps}
    direct_dep_refs = sorted(
        comp["bom-ref"]
        for comp in sbom_json.get("components", [])
        if comp.get("name", "").lower() in direct_dep_names and "bom-ref" in comp
    )
    dependencies = sbom_json.get("dependencies", [])
    dependencies.append({"dependsOn": direct_dep_refs, "ref": primary_ref})
    sbom_json["dependencies"] = dependencies


def _collect_thirdparty_deps(requires_dist: list, python_version: str) -> set[str]:
    """Extract 'thirdparty' dependency specifiers from project metadata."""

    import platform

    env = {
        "sys_platform": sys.platform,
        "extra": "thirdparty",
        "platform_system": platform.system(),
        "python_version": python_version,
    }

    dependencies = set()

    for require in requires_dist:
        req = Requirement(require)
        if req.marker and req.marker.evaluate(environment=env):
            dependencies.add(req.name + str(req.specifier))
    return dependencies
