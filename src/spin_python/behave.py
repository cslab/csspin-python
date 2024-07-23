# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
# All rights reserved.
# http://www.contact.de/

"""Module implementing the behave plugin for cs.spin"""

import contextlib
import os
import sys
from typing import Generator

from spin import config, die, info, option, setenv, sh, task, writetext
from spin.tree import ConfigTree

defaults = config(
    requires=config(
        spin=[
            "spin_python.python",
            "spin_ce.mkinstance",
            "spin_ce.ce_services",
        ],
        python=[
            "behave",
            "coverage",
        ],
    ),
    # Exclude the flaky tests in the defaults for now.
    # Will switch the default back to True as soon as
    # we have an easy way to set this in the CI.
    flaky=False,
    coverage=False,
    cov_report="python-at-coverage.xml",
    cov_config="setup.cfg",
    # Startup CE services before executing the tests
    services=True,
    # Default to concise and readable output
    opts=["--format=pretty", "--no-source"],
    # This is the default location of behave tests
    tests=["tests/accepttests"],
)


def configure(cfg: ConfigTree) -> None:
    """Add some runtime-dependent options"""
    if sys.platform == "win32":
        cfg.behave.opts.append("--tags=~linux")
    else:
        cfg.behave.opts.append("--tags=~windows")


def create_coverage_pth(cfg: ConfigTree) -> str:  # pylint: disable=unused-argument
    """Creating the coverage path file and returning its path"""
    # TODO: location of venv's site-packages should be available via
    # the property tree.
    site_packages = (
        sh(
            "python",
            "-c",
            'import sysconfig; print(sysconfig.get_path("purelib"))',
            capture_output=True,
            silent=True,
        )
        .stdout.decode()
        .strip()
    )
    coverage_pth_path = os.path.join(site_packages, "coverage.pth")
    info(f"Create {coverage_pth_path}")
    writetext(coverage_pth_path, "import coverage; coverage.process_startup()")
    return coverage_pth_path


@contextlib.contextmanager
def with_coverage(cfg: ConfigTree) -> Generator:
    """Context-manager enabling to run coverage"""
    coverage_pth = ""
    try:
        sh("coverage", "erase", may_fail=True)
        setenv(COVERAGE_PROCESS_START=cfg.behave.cov_config)
        coverage_pth = create_coverage_pth(cfg)
        yield
    finally:
        setenv(COVERAGE_PROCESS_START=None)
        if os.path.exists(coverage_pth):
            os.remove(coverage_pth)
        sh("coverage", "combine", may_fail=True)
        sh("coverage", "report", may_fail=True)
        sh("coverage", "xml", "-o", cfg.behave.cov_report, may_fail=True)


@contextlib.contextmanager
def noop(*args: str, **kwargs: dict) -> Generator:  # pylint: disable=unused-argument
    """Noop"""
    yield


def call_behave(cfg, instance, args) -> None:  # pylint: disable=unused-argument
    """Run the 'behave' command."""
    opts = cfg.behave.opts
    if not cfg.behave.flaky:
        opts.append("--tags=~flaky")
    sh("powerscript", "-m", "behave", *opts, *args, *cfg.behave.tests)


@task(when="cept")
def behave(
    cfg,
    instance: option("-i", "--instance"),  # noqa: F821
    coverage: option("-c", "--coverage", is_flag=True),  # noqa: F821
    args,
):
    # pylint: disable=missing-function-docstring
    from spin_ce import ce_services

    inst = os.path.abspath(instance or cfg.mkinstance.dbms)
    if not os.path.isdir(inst):
        die(f"Cannot find the CE instance '{inst}'.")
    setenv(CADDOK_BASE=inst)

    coverage_enabled = coverage or cfg.behave.coverage
    coverage_context = with_coverage if coverage_enabled else noop
    services_context = ce_services.with_ce_services if cfg.behave.services else noop
    with coverage_context(cfg):
        # This is a fast and dirty solution which provides CE services
        # for tests needing it.
        # TODO: replace with something more sensible
        # as soon as we've implemented it.
        with services_context(cfg):
            call_behave(cfg, instance, args)
