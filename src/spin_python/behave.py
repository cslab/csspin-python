# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com

"""Module implementing the behave plugin for cs.spin"""

import contextlib
import sys
from typing import Generator

from path import Path
from spin import config, die, info, option, rmtree, setenv, sh, task, writetext
from spin.tree import ConfigTree

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
            "spin_python.python",
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


def create_coverage_pth(cfg: ConfigTree) -> str:  # pylint: disable=unused-argument
    """Creating the coverage path file and returning its path"""
    coverage_pth_path = cfg.python.site_packages / "coverage.pth"
    info(f"Create {coverage_pth_path}")
    writetext(coverage_pth_path, "import coverage; coverage.process_startup()")
    return coverage_pth_path


@contextlib.contextmanager
def with_coverage(cfg: ConfigTree) -> Generator:
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
    cfg,
    instance: option("-i", "--instance"),  # noqa: F821
    coverage: option("-c", "--coverage", is_flag=True),  # noqa: F821
    debug: option("--debug", is_flag=True),  # noqa: F821
    with_test_report: option("--with-test-report", is_flag=True),  # noqa: F821,F722
    args,
):
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
    if cfg.loaded.get("spin_ce.mkinstance"):
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
