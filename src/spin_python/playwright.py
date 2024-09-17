# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the playwright plugin for cs.spin"""


from spin import Path, Verbosity, config, die, option, setenv, sh, task

defaults = config(
    requires=config(
        spin=[
            "spin_python.python",
            "spin_python.pytest",
        ],
        python=[
            "pytest-base-url",
            "pytest-playwright",
        ],
    ),
    browsers_path="{spin.cache}/playwright_browsers",
    browsers=[
        "chromium",
    ],
    coverage=False,
    coverage_opts=[
        "--cov-reset",
        "--cov",
        "--cov-report=term",
        "--cov-report=html",
        "--cov-report=xml",
    ],
    opts=["-m", "e2e"],
    tests=["cs", "tests"],
)


@task(when="cept")
def playwright(  # pylint: disable=missing-function-docstring
    cfg,
    instance: option("-i", "--instance", default=None),  # noqa: F821
    coverage: option("-c", "--coverage", is_flag=True),  # noqa: F821
    args,
):
    """Run the playwright tests with pytest."""
    setenv(PLAYWRIGHT_BROWSERS_PATH=cfg.playwright.browsers_path)

    opts = cfg.playwright.opts
    if cfg.verbosity == Verbosity.QUIET:
        opts.append("-q")
    if coverage or cfg.playwright.coverage:
        opts.extend(cfg.playwright.coverage_opts)

    for browser in cfg.playwright.browsers:
        opts.extend(["--browser", browser])

    # Run the browser download again, so that changes for
    # cfg.playwright.browsers don't require a new provision call. If the
    # browsers are already present it's more or less a noop.
    _download_playwright_browsers(cfg)

    if cfg.loaded.get("spin_ce.mkinstance"):
        if not (inst := Path(instance or cfg.mkinstance.dbms).absolute()).is_dir():
            die(f"Cannot find CE instance '{inst}'.")

        setenv(CADDOK_BASE=inst)
        sh("pytest", *opts, *args, *cfg.playwright.tests)
        setenv(CADDOK_BASE=None)
    else:
        sh("pytest", *opts, *args, *cfg.playwright.tests)


def _download_playwright_browsers(cfg):
    """Let playwright install the browsers"""
    sh(
        f"playwright install {' '.join(cfg.playwright.browsers)}",
        env={"PLAYWRIGHT_BROWSERS_PATH": cfg.playwright.browsers_path},
    )


def provision(cfg):
    """Install playwright browsers during provisioning"""
    _download_playwright_browsers(cfg)
