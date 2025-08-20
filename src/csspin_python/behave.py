# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
# https://www.contact-software.com
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


"""Module implementing the behave plugin for spin"""

import contextlib
import sys
from typing import Generator, Iterable

from csspin import config, die, info, option, rmtree, setenv, sh, task, writetext
from csspin.tree import ConfigTree
from path import Path

defaults = config(
    # Exclude the flaky tests in the defaults for now.
    # Will switch the default back to True as soon as
    # we have an easy way to set this in the CI.
    flaky=False,
    coverage=False,
    cov_report="python-at-coverage.xml",
    cov_config="setup.cfg",
    # Default to concise and readable output
    opts=[
        "--no-source",
        "--tags=~skip",
        "--format=pretty",
        "--no-skipped",
    ],
    report=config(
        name="cept_test_results.json",
        format="json.pretty",
    ),
    # This is the default location of behave tests
    tests=["tests/accepttests"],
    requires=config(
        spin=[
            "csspin_python.python",
        ],
        python=[
            "behave",
            "coverage",
        ],
    ),
)


def configure(cfg: ConfigTree) -> None:
    """Add some runtime-dependent options"""
    if sys.platform == "win32":
        cfg.behave.opts.append("--tags=~linux")
    else:
        cfg.behave.opts.append("--tags=~windows")


def create_coverage_pth(cfg: ConfigTree) -> Path:  # pylint: disable=unused-argument
    """Creating the coverage path file and returning its path"""
    coverage_pth_path: Path = cfg.python.site_packages / "coverage.pth"
    info(f"Create {coverage_pth_path}")
    writetext(coverage_pth_path, "import coverage; coverage.process_startup()")
    return coverage_pth_path


@contextlib.contextmanager
def with_coverage(cfg: ConfigTree) -> Generator[None, None, None]:
    """Context-manager enabling to run coverage"""
    coverage_pth = ""
    try:

        sh("coverage", "erase", check=False)
        setenv(COVERAGE_PROCESS_START=cfg.behave.cov_config)
        coverage_pth = create_coverage_pth(cfg)
        yield
    finally:
        setenv(COVERAGE_PROCESS_START=None)
        rmtree(coverage_pth)
        sh("coverage", "combine", check=False)
        sh("coverage", "report", check=False)
        sh("coverage", "xml", "-o", cfg.behave.cov_report, check=False)


@task(when="cept")
def behave(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    cfg: ConfigTree,
    instance: option(  # type: ignore[valid-type]
        "-i",  # noqa: F821
        "--instance",  # noqa: F821
        help="Directory of the CONTACT Elements instance.",  # noqa: F722
    ),
    coverage: option(  # type: ignore[valid-type]
        "-c",  # noqa: F821
        "--coverage",  # noqa: F821
        is_flag=True,
        help="Run the tests while collecting coverage.",  # noqa: F722
    ),
    debug: option(  # type: ignore[valid-type]
        "--debug", is_flag=True, help="Start debug server."  # noqa: F722,F821
    ),
    with_test_report: option(  # type: ignore[valid-type]
        "--with-test-report",  # noqa: F722
        is_flag=True,
        help="Create a test execution report.",  # noqa: F722
    ),
    args: Iterable[str],
) -> None:
    """Run Gherkin tests using behave."""
    # pylint: disable=missing-function-docstring
    coverage_enabled = coverage or cfg.behave.coverage
    coverage_context = with_coverage if coverage_enabled else contextlib.nullcontext
    opts = cfg.behave.opts
    if not cfg.behave.flaky:
        opts.append("--tags=~flaky")
    if with_test_report and cfg.behave.report.name and cfg.behave.report.format:
        opts = [
            f"--format={cfg.behave.report.format}",
            f"-o={cfg.behave.report.name}",
        ] + opts
    if cfg.loaded.get("csspin_ce.mkinstance"):
        inst = Path(instance or cfg.mkinstance.base.instance_location).absolute()
        if not (inst).is_dir():
            die(f"Cannot find the CE instance '{inst}'.")
        setenv(CADDOK_BASE=inst)

        cmd = ["powerscript"]
        if debug:
            cmd.append("--debugpy")

        with coverage_context(cfg):
            sh(*cmd, "-m", "behave", *opts, *args, *cfg.behave.tests)
    else:
        cmd = ["python"]
        if debug:
            cmd = ["debugpy"] + cfg.debugpy.opts

        with coverage_context(cfg):
            sh(*cmd, "-m", "behave", *opts, *args, *cfg.behave.tests)
