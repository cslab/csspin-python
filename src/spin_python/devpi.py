# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2020 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the devpi plugin for cs.spin"""


from spin import Command, config, die, exists, readyaml, setenv, sh, task

defaults = config(
    formats=["bdist_wheel"],
    url=None,
    user=None,
    requires=config(
        spin=["spin_python.python"],
        python=[
            "devpi-client",
            "keyring",
        ],
    ),
)


def init(cfg):  # pylint: disable=unused-argument
    """Sets some environment variables"""
    setenv(DEVPI_VENV="{python.venv}", DEVPI_CLIENTDIR="{spin.spin_dir}/devpi")


@task("devpi:upload")
def upload(cfg):
    """Upload project wheel to a package server."""
    if not cfg.devpi.user:
        die("devpi.user is required!")

    if exists(current_json := f"{cfg.spin.spin_dir}/devpi/current.json"):
        data = readyaml(current_json)
    else:
        data = {}

    devpi_ = Command("devpi")

    if data.get("index") != (url := cfg.devpi.url):
        if url == "None":
            die("devpi.url not provided!")
        devpi_("use", "-t", "yes", url)

    devpi_("login", cfg.devpi.user)
    devpi_(
        "upload",
        "-p",
        cfg.python.python,
        "--no-vcs",
        f"--wheel={','.join(cfg.devpi.formats)}",
    )


@task()
def devpi(cfg, args):
    """Run the 'devpi' command inside the project's virtual environment.

    All command line arguments are simply passed through to 'devpi'.

    """
    if cfg.devpi.url:
        sh("devpi", "use", cfg.devpi.url)
    if cfg.devpi.user:
        sh("devpi", "login", cfg.devpi.user)

    sh("devpi", *args)
