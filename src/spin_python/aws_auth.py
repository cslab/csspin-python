# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the aws_auth plugin for cs.spin"""

import configparser
import os

from spin import Path, config, debug, die, exists, info, interpolate1

defaults = config(
    aws_role_arn="arn:aws:iam::373369985286:role/cs-central1-codeartifact-ecr-read-role",
    aws_region="eu-central-1",
    aws_role_session_name="CodeArtifactSession",
    aws_codeartifact_domain="contact",
    aws_key_duration=3600,
    keycloak_url="https://login.contact-cloud.com/realms/contact/protocol/openid-connect/token",
    client_id="central1-auth-oidc-read",
)


def configure(cfg):  # pylint: disable=too-many-statements
    """Configure the plugin and apply changes to the configuration tree"""
    # Could be useful in CI e.g. when you want to build docs
    # and need to include this plugin in spinfile
    # without using it's functionality
    if os.environ.get("AWS_AUTH_DISABLE"):
        info("AWS_AUTH_DISABLE is set, ignoring aws_auth plugin")
        return

    from sys import platform

    try:
        import boto3
        import requests
        from botocore.exceptions import ClientError
    except ImportError:
        die(
            "Failed to import required modules. Please install them by setting:"
            "\n\tplugin_packages:\n\t\t- python[aws_auth]\n"
            "in your project's spinfile.yaml"
        )

    cfg.aws_auth.client_secret = os.environ.get("KEYCLOAK_CLIENT_SECRET")
    if not cfg.aws_auth.client_secret:
        die(
            "Neither aws_auth.client_secret config"
            "entry nor KEYCLOAK_CLIENT_SECRET environment variable was found."
        )

    def get_keycloak_access_token(keycloak_url, client_id, client_secret):
        """
        Obtain the Keycloak access token using client credentials.
        """
        debug("Requesting Keycloak access token...")
        payload = {
            "grant_type": "client_credentials",
            "client_id": client_id,
            "client_secret": client_secret,
        }

        try:
            response = requests.post(keycloak_url, data=payload, timeout=15)
            response.raise_for_status()
            data = response.json()
            access_token = data.get("access_token")
            if not access_token:
                raise ValueError("Response doesn't contain access_token")
        except (ValueError, requests.exceptions.RequestException) as e:
            die(f"Failed to fetch Keycloak access token: {e}")

        return access_token

    def assume_aws_role_with_web_identity(
        keycloak_access_token,
        role_arn,
        role_session_name,
        region,
        key_duration_seconds,
    ):
        """
        Request AWS STS credentials using the Keycloak token as a web identity.
        """
        debug("Requesting AWS STS credentials...")
        sts_client = boto3.client("sts", region_name=region)
        try:
            sts_response = sts_client.assume_role_with_web_identity(
                RoleArn=role_arn,
                RoleSessionName=role_session_name,
                WebIdentityToken=keycloak_access_token,
                DurationSeconds=key_duration_seconds,
            )
            credentials = sts_response.get("Credentials", {})
            if not (
                credentials.get("AccessKeyId")
                and credentials.get("SecretAccessKey")
                and credentials.get("SessionToken")
            ):
                raise ValueError("Incomplete AWS credentials received")
        except (ValueError, ClientError) as e:
            die(f"Failed to assume AWS role with web identity: {e}")

        return credentials

    def get_codeartifact_auth_token(credentials, domain, region):
        """
        Retrieve the AWS CodeArtifact authentication token using temporary AWS credentials.
        """
        debug("Requesting CodeArtifact authentication token...")
        codeartifact_client = boto3.client(
            "codeartifact",
            region_name=region,
            aws_access_key_id=credentials.get("AccessKeyId"),
            aws_secret_access_key=credentials.get("SecretAccessKey"),
            aws_session_token=credentials.get("SessionToken"),
        )

        try:
            response = codeartifact_client.get_authorization_token(domain=domain)
            auth_token = response.get("authorizationToken")
            if not auth_token:
                raise ValueError("Failed to retrieve CodeArtifact authentication token")
        except (ValueError, ClientError) as e:
            die(f"Failed to retrieve CodeArtifact authentication token: {e}")

        return auth_token

    keycloak_access_token = get_keycloak_access_token(
        cfg.aws_auth.keycloak_url, cfg.aws_auth.client_id, cfg.aws_auth.client_secret
    )

    credentials = assume_aws_role_with_web_identity(
        keycloak_access_token,
        cfg.aws_auth.aws_role_arn,
        cfg.aws_auth.aws_role_session_name,
        cfg.aws_auth.aws_region,
        cfg.aws_auth.aws_key_duration,
    )

    codeartifact_auth_token = get_codeartifact_auth_token(
        credentials, cfg.aws_auth.aws_codeartifact_domain, cfg.aws_auth.aws_region
    )

    domain_owner = cfg.aws_auth.aws_role_arn.split(":")[3]

    cfg.aws_auth.codeartifact_auth_token = codeartifact_auth_token
    cfg.python.index_url = (
        f"https://aws:{codeartifact_auth_token}@"
        f"{cfg.aws_auth.aws_codeartifact_domain}-{domain_owner}"
        f".d.codeartifact.{cfg.aws_auth.aws_region}.amazonaws.com/pypi/elements/simple/"
    )

    pipconf = interpolate1(cfg.python.venv) / Path(
        "pip.ini" if platform == "win32" else "pip.conf"
    )
    if exists(pipconf):
        # Need to update pip.conf with the new index_url
        # for "spin run pip ..." to use the right index and
        # not the default one
        _update_pipconf_url(pipconf, cfg.python.index_url)


def _update_pipconf_url(filename, url):
    """Upates the python.index_url in the pip.conf file with the new value"""
    info(f"Updating python.index_url in {filename} with a fresh token...")
    config_parser = configparser.ConfigParser()
    config_parser.read(filename)
    if not config_parser.has_section("global"):
        config_parser.add_section("global")
    option = (
        "index-url" if config_parser.has_option("global", "index-url") else "index_url"
    )
    config_parser.set("global", option, url)
    with open(filename, mode="w", encoding="utf-8") as f:
        config_parser.write(f)
