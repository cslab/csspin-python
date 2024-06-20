# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2021 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the piptools plugin for cs.spin"""

import difflib
import itertools

from spin import (
    config,
    die,
    exists,
    info,
    is_up_to_date,
    readlines,
    sh,
    task,
    writelines,
)

from spin_python.python import ProvisionerProtocol

defaults = config(
    requires=config(
        spin=["spin_python.python"],
        python=["setuptools", "pip-tools"],
    ),
    hashes=False,
    requirements="requirements-{platform.kind}.txt",
    requirements_sources=["setup.py", "setup.cfg"],
    spinreqs="spin-reqs-{platform.kind}.txt",
    extras=[],
    spinreqs_in="{piptools.spinreqs}.in",
    editable_options=[
        "--no-deps",
        "--no-build-isolation",
    ],
    pip_compile=config(
        cmd="compile",
        options_hash=[
            "--generate-hashes",
            "--reuse-hashes",
        ],
        options=[
            "--allow-unsafe",
            "--header",
            "--annotate",
            "--no-emit-options",
            "--resolver=backtracking",
        ],
        env=config(
            CUSTOM_COMPILE_COMMAND="spin --provision",
            PYTHONWARNINGS="ignore:setuptools",
        ),
    ),
    pip_sync=config(
        cmd="sync",
        options=[],
        env=config(
            PYTHONWARNINGS="ignore:setuptools",
        ),
    ),
    prerequisites=["pip-tools"],
)


def piptools_cmd(cfg, cmd, *args, **kwargs):
    """Executes the piptools command using given arguments"""
    sh(cfg.python.python, "-mpiptools", cmd, cfg.quietflag, *args, **kwargs)


def pip_compile(cfg, *args):  # pylint: disable=missing-function-docstring
    # TODO: add reasonable docstring
    options = cfg.piptools.pip_compile.options
    if cfg.piptools.hashes:
        options.extend(cfg.piptools.pip_compile.options_hash)
    piptools_cmd(
        cfg,
        cfg.piptools.pip_compile.cmd,
        *options,
        *args,
        env=cfg.piptools.pip_compile.env,
    )


class PiptoolsProvisioner(ProvisionerProtocol):
    """Class providing the necessary functions to act as Python provisioner"""

    def __init__(self, cfg):
        self.cfg = cfg
        self.spinreqs = set()
        self.locks_updated = False

    def prerequisites(self, cfg):
        # use python -m pip otherwise this could lead to permission issues under
        # windows
        sh(
            cfg.python.python,
            "-m",
            "pip",
            "install",
            cfg.quietflag,
            *cfg.piptools.prerequisites,
        )

    def lock(self, cfg):
        if not is_up_to_date(
            cfg.piptools.requirements, cfg.piptools.requirements_sources
        ):
            extra_args = []
            for extra in cfg.python.extras:
                extra_args.append(f"--extra={extra}")
            for extra in cfg.piptools.extras:
                extra_args.append(f"--extra={extra}")
            pip_compile(cfg, *extra_args, "-o", cfg.piptools.requirements)
            self.locks_updated = True

    def add(self, req, devpackage=False):
        if req.startswith("-e") and self.cfg.piptools.hashes:
            die("Hashed dependencies are incompatible with editable installs.")
        self.spinreqs.add(req)

    def lock_extras(self, cfg):
        spinreqs = list(self.spinreqs)
        spinreqs.sort()
        newtext = [f"{extra}\n" for extra in spinreqs]
        oldtext = []
        if exists(cfg.piptools.spinreqs_in):
            oldtext = readlines(cfg.piptools.spinreqs_in)
        if newtext != oldtext or not exists(cfg.piptools.spinreqs):
            # Show a nice diff of the updated .in file
            print(
                "".join(
                    difflib.context_diff(
                        oldtext, newtext, fromfile="before", tofile="after"
                    )
                )
            )
            writelines(cfg.piptools.spinreqs_in, newtext)
            pip_compile(cfg, cfg.piptools.spinreqs_in, "-o", cfg.piptools.spinreqs)
            self.locks_updated = True

    def sync(self, cfg):
        if self.locks_updated and self.have_wheelhouse(cfg):
            info("Updating the wheelhouse!")
            self.wheelhouse(cfg)
        options = list(cfg.piptools.pip_sync.options)
        if self.have_wheelhouse(cfg):
            options.append("--no-index")
        piptools_cmd(
            cfg,
            cfg.piptools.pip_sync.cmd,
            *options,
            cfg.piptools.requirements,
            cfg.piptools.spinreqs,
            env=cfg.piptools.pip_sync.env,
        )

    def install(self, cfg):
        if exists("setup.py"):
            sh(
                cfg.python.python,
                "-mpip",
                "install",
                cfg.quietflag,
                *cfg.piptools.editable_options,
                "-e",
                ".",
            )

    def have_wheelhouse(self, cfg):
        return exists(cfg.python.wheelhouse)

    def wheelhouse(self, cfg):
        sh(
            cfg.python.python,
            "-mpip",
            "--exists-action",
            "b",
            "download",
            "-d",
            cfg.python.wheelhouse,
            "-r",
            cfg.piptools.requirements,
            "-r",
            cfg.piptools.spinreqs,
        )


def configure(cfg):
    """Configure the piptools plugin"""
    # We simply overwrite the default provisioner of the Python plugin
    # to replace the dependency management strategy.
    cfg.python.provisioner = PiptoolsProvisioner(cfg)


@task("python:wheelhouse")
def wheelhouse(cfg):
    """Download wheels to speed up provisioning new environments.

    Downloads the exact versions packages specified in the lock files
    into the wheelhouse for this project.
    """
    cfg.python.provisioner.wheelhouse(cfg)


@task("python:upgrade")
def python_upgrade(cfg, args):
    """Upgrade packages using pip-compile.

    With no arguments, upgrade all packages. If arguments are given,
    they are interpreted as the names of packages that are to be
    updated.

    Note that python:upgrade just modifies the lock files. To actually
    install upgrades, use 'spin --provision'. When a wheelhouse is
    used, the upgraded packages must be downloaded first using
    'python:wheelhouse'.
    """
    if not args:
        args = ["--upgrade"]
    else:
        args = list(
            itertools.chain.from_iterable(
                itertools.product(("--upgrade-package",), args)
            )
        )
    pip_compile(cfg, "-o", cfg.piptools.requirements, *args)
    pip_compile(cfg, cfg.piptools.spinreqs_in, "-o", cfg.piptools.spinreqs, *args)
