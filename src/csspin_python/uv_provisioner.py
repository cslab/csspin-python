# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
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

"""
Plugin to replace certain things of the csspin_python.python plugin with the
tool ``uv``. Can only be used if the ``uv`` extra of csspin_python has been
installed.
"""

import shutil
import subprocess
from typing import Union

try:
    import tomllib
except ImportError:
    # Fallback for spin has been installed with python < 3.11
    import tomli as tomllib

import tomli_w
from csspin import Command, Path, Verbosity, config, die, info, interpolate1, setenv
from csspin.tree import ConfigTree

from csspin_python.python import SimpleProvisioner

defaults = config(
    enabled=False,
    uv_python_data="{spin.data}/uv_python",
    uv_toml_path="{python.venv}/uv.toml",
    requires=config(
        spin=[
            "csspin_python.python",
        ],
    ),
)


def venv_hook(cfg: ConfigTree) -> None:
    """Things to do right after venv creation."""
    _configure_uv_toml(cfg)
    setenv(UV_CONFIG_FILE=cfg.uv_provisioner.uv_toml_path)


def configure(cfg: ConfigTree) -> None:
    """Configure the uv_provisioner plugin."""
    if interpolate1(cfg.uv_provisioner.enabled).lower() == "true":
        cfg.python.provisioner = SimpleUvProvisioner(cfg)
        setenv(
            UV_PYTHON_INSTALL_DIR=interpolate1(cfg.uv_provisioner.uv_python_data),
        )
        if cfg.python.use:
            cfg.python.interpreter = shutil.which(interpolate1(cfg.python.interpreter))
        else:
            if interpreter_path := _get_uv_python(cfg, True):
                cfg.python.interpreter = interpreter_path
            else:
                # No uv provisioned python found, set to an empty string to
                # force provisioning
                cfg.python.interpreter = ""

        if cfg.python.aws_auth.enabled:
            # In case we use aws_auth the index-url might have changed
            _update_index_url_in_toml(cfg)


def _get_uv_python(cfg: ConfigTree, ignore_errors: bool = False) -> Union[Path, None]:
    """Use uv to find its provisioned python interpreter."""
    # We cannot put this import top-level as "spin cleanup" might not work
    # otherwise.
    from uv import find_uv_bin

    cmd = [
        find_uv_bin(),
        "python",
        "find",
        "--no-project",
        "--system",
        "--managed-python",
        cfg.python.version,
    ]
    try:
        out = subprocess.check_output(
            cmd, encoding="utf-8", stderr=subprocess.DEVNULL if ignore_errors else None
        )
        interpreter = out.strip()
        return Path(interpreter)
    except subprocess.CalledProcessError as ex:
        if not ignore_errors:
            die(ex)
    return None


class SimpleUvProvisioner(SimpleProvisioner):
    """
    Drop-in replacement for the SimpleProvisioner that uses ``uv`` for creating
    the environment and installing the requirements.

    Especially when installing Python packages, the ``SimpleUvProvisioner`` is
    much faster than the ``SimpleProvisioner``.
    """

    def __init__(self, cfg: ConfigTree) -> None:
        super().__init__(cfg)

        from uv import find_uv_bin

        uv_bin = find_uv_bin()

        if cfg.verbosity == Verbosity.QUIET:
            verbosity = "-q"
        elif cfg.verbosity == Verbosity.DEBUG:
            verbosity = "-v"
        else:
            verbosity = None

        self._uv_cmd = Command(
            uv_bin,
            verbosity,
        )
        self._install_command = Command(
            *self._uv_cmd._cmd,
            "pip",
            "install",
            *[f"--constraint={constraint}" for constraint in cfg.python.constraints],
        )

    def provision_python(self, cfg: ConfigTree) -> None:
        self._uv_cmd(
            "python",
            "install",
            cfg.python.version,
            "--no-bin",
            "--no-registry",
        )
        cfg.python.interpreter = _get_uv_python(cfg)
        info(f"Using '{cfg.python.interpreter}' as interpreter")

    def provision_venv(self, cfg: ConfigTree) -> None:
        setenv(UV_PROJECT_ENVIRONMENT=cfg.python.venv)
        self._uv_cmd(
            "venv",
            f"--python={cfg.python.interpreter}",
            cfg.python.venv,
        )

    def prerequisites(self, cfg: ConfigTree) -> None:
        self._uv_cmd("pip", "install", "pip")


def _configure_uv_toml(cfg: ConfigTree) -> None:
    """
    Create a config file for uv, similar to the pip.conf of
    csspin_python.python, since `uv` pip won't respect the pip.conf.
    """
    toml_content = tomllib.loads(cfg.uv_provisioner.uv_toml or "")
    if "index-url" not in toml_content:
        toml_content["index-url"] = cfg.python.index_url
    else:
        toml_content["index-url"] = toml_content.get("index-url", cfg.python.index_url)

    with open(cfg.uv_provisioner.uv_toml_path, mode="wb") as fd:
        tomli_w.dump(toml_content, fd)


def _update_index_url_in_toml(cfg: ConfigTree) -> None:
    """
    Update the index-url in the uv.toml in case it changed.
    """
    if (uv_toml_path := interpolate1(cfg.uv_provisioner.uv_toml_path)).exists():
        with open(uv_toml_path, mode="r+b") as fd:
            toml_content = tomllib.load(fd)
            if toml_content.get("index-url") != cfg.python.index_url:
                toml_content["index-url"] = cfg.python.index_url
                tomli_w.dump(toml_content, fd)
