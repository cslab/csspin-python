# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

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
CS_AWS_OIDC_CLIENT_ID = os.getenv("CS_AWS_OIDC_CLIENT_ID")
CS_AWS_OIDC_CLIENT_SECRET = os.getenv("CS_AWS_OIDC_CLIENT_SECRET")


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
@pytest.mark.skipif(not CS_AWS_OIDC_CLIENT_ID, reason="AWS OIDC client ID not set")
@pytest.mark.skipif(
    not CS_AWS_OIDC_CLIENT_SECRET, reason="AWS OIDC client secret not set"
)
@pytest.mark.skipif(not PYTHON_EXISTS, reason="python not in PATH.")
def test_aws_auth(tmp_path):
    """
    Test whether the pip configuration file is created with the correct
    index-url and can be updated with the AWS credentials.
    """
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
