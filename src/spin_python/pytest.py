# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
# All rights reserved.
# http://www.contact.de/

"""Module implementing the pytest plugin for cs.spin"""

import contextlib
import os
from typing import Generator

from spin import config, die, option, setenv, sh, task

defaults = config(
    requires=config(
        spin=[
            "spin_python.python",
            "spin_ce.mkinstance",
            "spin_ce.ce_services",
        ],
        python=[
            "pytest",
            "pytest-cov",
            "psutil",
        ],
    ),
    coverage=False,
    opts=[],
    coverage_opts=[
        "--cov-reset",
        "--cov",
        "--cov-report=term",
        "--cov-report=html",
        "--cov-report=xml",
    ],
    # Strong convention @CONTACT
    tests=["cs", "tests"],
    services=False,
)


@contextlib.contextmanager
def noop(*args: str, **kwargs: dict) -> Generator:  # pylint: disable=unused-argument
    """Noop"""
    yield


@task(when="test")
def pytest(  # pylint: disable=missing-function-docstring
    cfg,
    instance: option("-i", "--instance"),  # noqa: F821
    coverage: option("-c", "--coverage"),  # noqa: F821
    args,
):
    """Run the 'pytest' command."""
    import ce_services

    inst = os.path.abspath(instance or cfg.mkinstance.dbms)
    if not os.path.isdir(inst):
        die(f"Cannot find the CE instance '{inst}'.")

    opts = cfg.pytest.opts
    if coverage or cfg.pytest.coverage:
        opts.extend(cfg.pytest.coverage_opts)
    setenv(CADDOK_BASE=inst)
    services_context = ce_services.with_ce_services if cfg.pytest.services else noop
    with services_context(cfg):
        sh("pytest", *opts, *args, *cfg.pytest.tests)
    setenv(CADDOK_BASE=None)
