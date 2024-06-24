# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2020 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the devpi plugin for cs.spin"""

import os

from spin import (
    Command,
    config,
    exists,
    get_tree,
    interpolate1,
    readyaml,
    setenv,
    sh,
    task,
)

defaults = config(
    formats=["bdist_wheel"],
    requires=config(
        spin=["spin_python.python"],
        python=["devpi-client", "keyring"],
    ),
)


def prepare_environment():
    """Sets some environment variables"""
    setenv(DEVPI_VENV="{python.venv}", DEVPI_CLIENTDIR="{spin.spin_dir}/devpi")


@task()
def stage():
    """Upload project wheel to the staging area."""
    prepare_environment()
    data = {}
    devpi = Command("devpi")  # pylint: disable=redefined-outer-name
    if exists("{spin.spin_dir}/devpi/current.json"):
        data = readyaml("{spin.spin_dir}/devpi/current.json")
    if data.get("index", "") != interpolate1("{devpi.stage}"):
        devpi("use", "-t", "yes", "{devpi.stage}")
    devpi("login", "{devpi.user}")
    python = os.path.abspath(get_tree().python.python)
    devpi(
        "upload",
        "-p",
        python,
        "--no-vcs",
        "--formats={','.join(devpi.formats)}",
    )


@task()
def devpi(cfg, args):
    """Run the 'devpi' command inside the project's virtual environment.

    All command line arguments are simply passed through to 'devpi'.

    """
    prepare_environment()
    if hasattr(cfg.devpi, "url"):
        sh("devpi", "use", cfg.devpi.url)
    if hasattr(cfg.devpi, "user"):
        sh("devpi", "login", cfg.devpi.user)

    sh("devpi", *args)
