# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/
# pylint: disable=no-member


"""
Module implementing 'aws_auth' extra related acceptance tests for csspin-python
"""

import os
import shlex
import shutil
import subprocess
import sys

import pytest

PYTHON_EXISTS = shutil.which("python")


def execute_spin(yaml, env, path="tests/acceptance/yamls", cmd=""):
    """Helper function to execute spin and return the output"""
    try:
        cmd = shlex.split(
            f"spin -q -p spin.data={env} -C {path} --env {env} -f {yaml} {cmd}",
            posix=sys.platform != "win32",
        )
        print(subprocess.list2cmdline(cmd))
        return subprocess.check_output(
            cmd,
            encoding="utf-8",
            stderr=subprocess.PIPE,
        ).strip()
    except subprocess.CalledProcessError as ex:
        print(ex.stdout)
        print(ex.stderr)
        raise


@pytest.mark.acceptance
@pytest.mark.skipif(not PYTHON_EXISTS, reason="python not in PATH.")
@pytest.mark.parametrize(
    "env_vars",
    [
        pytest.param(
            {"CS_AWS_OIDC_CLIENT_SECRET": os.getenv("CS_AWS_OIDC_CLIENT_SECRET")},
            id="default_aws_credentials",
            marks=pytest.mark.skipif(
                not os.getenv("CS_AWS_OIDC_CLIENT_SECRET"),
                reason="'CS_AWS_OIDC_CLIENT_SECRET' not set in environment",
            ),
        ),
        pytest.param(
            {
                "CS_AWS_OIDC_CLIENT_SECRET": os.getenv(
                    "CS_EXTRA_AWS_OIDC_CLIENT_SECRET"
                ),
                "SPIN_TREE_PYTHON__AWS_AUTH__CLIENT_ID": os.getenv(
                    "CS_EXTRA_AWS_OIDC_CLIENT_ID"
                ),
                "SPIN_TREE_PYTHON__AWS_AUTH__ROLE_ARN": os.getenv(
                    "CS_EXTRA_AWS_OIDC_ROLE_ARN"
                ),
            },
            id="custom_aws_credentials",
            marks=pytest.mark.skipif(
                not all(
                    (
                        os.getenv("CS_EXTRA_AWS_OIDC_CLIENT_SECRET"),
                        os.getenv("CS_EXTRA_AWS_OIDC_CLIENT_ID"),
                        os.getenv("CS_EXTRA_AWS_OIDC_ROLE_ARN"),
                    )
                ),
                reason="'CS_EXTRA_AWS_OIDC_CLIENT_SECRET',"
                " 'CS_EXTRA_AWS_OIDC_CLIENT_ID', 'CS_EXTRA_AWS_OIDC_ROLE_ARN'"
                " not set in environment",
            ),
        ),
    ],
)
def test_aws_auth(tmp_path, env_vars, monkeypatch):
    """
    Test whether the pip configuration file is created with the correct
    index-url and can be updated with the AWS credentials.
    """
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)

    import configparser

    if sys.platform == "win32":
        pipconf = tmp_path / ".spin" / "venv" / "pip.ini"
    else:
        pipconf = tmp_path / ".spin" / "venv" / "pip.conf"
    assert not pipconf.exists(), "pip configuration file already exists"

    def get_index_url(cfg):
        return cfg["global"].get("index-url", cfg["global"].get("index_url", ""))

    # == Initial provision, ensuring pip.conf is created
    execute_spin("python_aws_auth.yaml", tmp_path, cmd="provision")
    assert pipconf.exists(), "pip configuration file was not created"
    config = configparser.ConfigParser()
    config.read(pipconf)
    assert get_index_url(config).startswith(
        "https://aws:"
    ), "index-url does not start with 'https://aws:'"

    # == Check that a second provision doesn't change the index-url
    initial_index_url = get_index_url(config)
    execute_spin("python_aws_auth.yaml", tmp_path, cmd="provision")
    config.read(pipconf)
    assert initial_index_url == get_index_url(
        config
    ), "index-url changed after second provision"

    # == Check if the update mechanism works
    execute_spin(
        "python_aws_auth.yaml",
        tmp_path,
        cmd="-p python.aws_auth.key_duration=0 provision",
    )
    config.read(pipconf)
    assert get_index_url(config).startswith(
        "https://aws:"
    ), "index-url does not start with 'https://aws:'"
    assert initial_index_url != get_index_url(
        config
    ), "index-url did not change after update"
