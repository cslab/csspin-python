# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2020 CONTACT Software GmbH
# https://www.contact-software.com/
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

"""Module implementing the devpi plugin for spin"""


from typing import Iterable

from csspin import Command, config, die, exists, readyaml, setenv, sh, task
from csspin.tree import ConfigTree

defaults = config(
    formats=["bdist_wheel"],
    url=None,
    user=None,
    requires=config(
        spin=["csspin_python.python"],
        python=[
            "devpi-client",
            "keyring",
        ],
    ),
)


def init(cfg: ConfigTree) -> None:  # pylint: disable=unused-argument
    """Sets some environment variables"""
    setenv(DEVPI_VENV="{python.venv}", DEVPI_CLIENTDIR="{spin.spin_dir}/devpi")


@task("devpi:upload")
def upload(cfg: ConfigTree) -> None:
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
def devpi(cfg: ConfigTree, args: Iterable[str]) -> None:
    """Run the 'devpi' command inside the project's virtual environment.

    All command line arguments are simply passed through to 'devpi'.

    """
    if cfg.devpi.url:
        sh("devpi", "use", cfg.devpi.url)
    if cfg.devpi.user:
        sh("devpi", "login", cfg.devpi.user)

    sh("devpi", *args)
