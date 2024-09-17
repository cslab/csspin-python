# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the pytest plugin for cs.spin"""


from spin import Path, Verbosity, config, die, option, setenv, sh, task

defaults = config(
    requires=config(
        spin=["spin_python.python"],
        python=[
            "pytest",
            "pytest-cov",
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
)


@task(when="test")
def pytest(  # pylint: disable=missing-function-docstring
    cfg,
    instance: option("-i", "--instance", default=None),  # noqa: F821
    coverage: option("-c", "--coverage", is_flag=True),  # noqa: F821
    args,
):
    """Run the 'pytest' command."""
    opts = cfg.pytest.opts
    if cfg.verbosity == Verbosity.QUIET:
        opts.append("-q")
    if coverage or cfg.pytest.coverage:
        opts.extend(cfg.pytest.coverage_opts)

    if cfg.loaded.get("spin_ce.mkinstance"):
        if not (inst := Path(instance or cfg.mkinstance.dbms).absolute()).is_dir():
            die(f"Cannot find CE instance '{inst}'.")

        setenv(CADDOK_BASE=inst)
        sh("pytest", *opts, *args, *cfg.pytest.tests)
        setenv(CADDOK_BASE=None)
    else:
        sh("pytest", *opts, *args, *cfg.pytest.tests)
