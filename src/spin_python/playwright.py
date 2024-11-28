# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2024 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the playwright plugin for cs.spin"""


from spin import Path, Verbosity, config, die, option, setenv, sh, task

defaults = config(
    browsers_path="{spin.data}/playwright_browsers",
    browsers=["chromium"],
    coverage=False,
    coverage_opts=[
        "--cov-reset",
        "--cov",
        "--cov-report=term",
        "--cov-report=html",
        "--cov-report=xml:{playwright.coverage_report}",
    ],
    coverage_report="python-playwright-coverage.xml",
    opts=["-m", "e2e"],
    tests=["cs", "tests"],  # Strong convention @CONTACT
    test_report="playwright.xml",
    requires=config(
        spin=[
            "spin_python.debugpy",
            "spin_python.python",
            "spin_python.pytest",
        ],
        python=[
            "pytest-base-url",
            "pytest-playwright",
        ],
    ),
)


@task(when="cept")
def playwright(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    cfg,
    instance: option("-i", "--instance", default=None),  # noqa: F821
    coverage: option("-c", "--coverage", is_flag=True),  # noqa: F821
    debug: option("--debug", is_flag=True),  # noqa: F821
    with_test_report: option("--with-test-report", is_flag=True),  # noqa: F821,F722
    args,
):
    """Run the playwright tests with pytest."""
    setenv(
        PLAYWRIGHT_BROWSERS_PATH=cfg.playwright.browsers_path,
        PACKAGE_NAME=cfg.spin.project_name,
    )

    opts = cfg.playwright.opts
    if cfg.verbosity == Verbosity.QUIET:
        opts.append("-q")
    if with_test_report and cfg.playwright.test_report:
        opts.append(f"--junitxml={cfg.playwright.test_report}")
    if coverage or cfg.playwright.coverage:
        opts.extend(cfg.playwright.coverage_opts)
        setenv(PLAYWRIGHT_COVERAGE=1)

    for browser in cfg.playwright.browsers:
        opts.extend(["--browser", browser])

    if debug:
        cmd = f"debugpy {' '.join(cfg.debugpy.opts)} -m pytest".split()
    else:
        cmd = ["pytest"]

    # Run the browser download again, so that changes for
    # cfg.playwright.browsers don't require a new provision call. If the
    # browsers are already present it's more or less a noop.
    _download_playwright_browsers(cfg)

    if cfg.loaded.get("spin_ce.mkinstance"):
        if not (
            inst := Path(instance or cfg.mkinstance.base.instance_location).absolute()
        ).is_dir():
            die(f"Cannot find CE instance '{inst}'.")

        setenv(CADDOK_BASE=inst)
        sh(*cmd, *opts, *args, *cfg.playwright.tests)
        setenv(CADDOK_BASE=None)
    else:
        sh(*cmd, *opts, *args, *cfg.playwright.tests)


def _download_playwright_browsers(cfg):
    """Let playwright install the browsers"""
    sh(
        f"playwright install {' '.join(cfg.playwright.browsers)}",
        env={"PLAYWRIGHT_BROWSERS_PATH": cfg.playwright.browsers_path},
    )


def provision(cfg):
    """Install playwright browsers during provisioning"""
    _download_playwright_browsers(cfg)
