# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2025 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the unit tests for csspin_python"""

import os
import re
import sys
from contextlib import nullcontext
from subprocess import CalledProcessError
from unittest import mock

import pytest
from click import Abort

# Mock `csspin.task` away as the import fails otherwise. Patched with a
# passthrough decorator factory (not a plain MagicMock) so that
# '@task(...)'-decorated functions like 'wheel' remain the real function
# object and can be tested directly.
with mock.patch("csspin.task", lambda *args, **kwargs: (lambda func: func)):
    from csspin_python.python import (
        Verbosity,
        _check_aws_token_validity,
        _check_venv,
        _configure_pipconf,
        _obfuscate_index_url,
        _split_requirement_option,
        get_project_metadata,
        python_env,
        wheel,
    )


@pytest.mark.parametrize(
    "pipconf,expected_index",
    (
        ("[global]\ntimeout=10", "https://pypi.org/simple"),
        ("[install]\ntimeout=10", "https://pypi.org/simple"),
        (
            "[global]\ntimeout=10\nindex_url=https://example.com/simple",
            "https://example.com/simple",
        ),
        (
            "[global]\ntimeout=10\nindex-url=https://example.com/simple2",
            "https://example.com/simple2",
        ),
    ),
)
def test__configure_pipconf(tmp_path, pipconf, expected_index):
    """
    Test whether _configure_pipconf handles the index_url properly.
    """
    config_file = (
        tmp_path / "pip.conf" if sys.platform != "win32" else tmp_path / "pip.ini"
    )
    config_file.touch()
    cfg_mock = mock.MagicMock()
    cfg_mock.python.index_url = "https://pypi.org/simple"
    cfg_mock.python.extra_index_urls = []
    cfg_mock.python.pipconf = pipconf
    cfg_mock.python.venv = tmp_path

    _configure_pipconf(cfg_mock)

    with open(config_file, encoding="utf-8") as fd:
        content = fd.read()
        assert re.search(r"index[-_]url", content)
        for line in content.splitlines():
            if re.match(r"^index[-_]url", line):
                assert expected_index in line


@pytest.mark.parametrize(
    "pipconf_template,configured_extra_index_urls,expected_urls",
    (
        pytest.param(
            "[global]\ntimeout=10",
            [],
            set(),
            id="none_configured",
        ),
        pytest.param(
            "[global]\ntimeout=10",
            [
                "https://example.com/extra1/simple",
                "https://example.com/extra2/simple",
            ],
            {
                "https://example.com/extra1/simple",
                "https://example.com/extra2/simple",
            },
            id="writes_multiple",
        ),
        pytest.param(
            "[global]\nextra-index-url = https://gitlab.example/simple",
            ["https://aws:TOKEN@host/pypi/stb/simple"],
            {"https://aws:TOKEN@host/pypi/stb/simple"},
            id="ignores_template_value",
        ),
        pytest.param(
            "[global]\n"
            "extra_index_url = https://a.example/simple\n"
            "extra-index-url = https://b.example/simple",
            [],
            set(),
            id="drops_both_spellings_when_none_configured",
        ),
    ),
)
def test__configure_pipconf_extra_index_url(
    tmp_path, pipconf_template, configured_extra_index_urls, expected_urls
):
    """
    Test that _configure_pipconf writes 'python.extra_index_urls' verbatim
    and ignores/drops whatever 'python.pipconf' already declares under
    either key spelling, since extra index urls must be configured via
    'python.extra_index_urls', not 'python.pipconf'.
    """
    config_file = (
        tmp_path / "pip.conf" if sys.platform != "win32" else tmp_path / "pip.ini"
    )
    config_file.touch()
    cfg_mock = mock.MagicMock()
    cfg_mock.python.index_url = "https://pypi.org/simple"
    cfg_mock.python.extra_index_urls = configured_extra_index_urls
    cfg_mock.python.pipconf = pipconf_template
    cfg_mock.python.venv = tmp_path

    _configure_pipconf(cfg_mock)

    content = config_file.read_text(encoding="utf-8")
    if expected_urls:
        for url in expected_urls:
            assert url in content
        # Exactly one of the two key spellings should be present, otherwise
        # pip's config loader (which normalizes '-'/'_') only honors one.
        assert len(re.findall(r"(?m)^extra[-_]index[-_]url\s*=", content)) == 1
    else:
        assert not re.search(r"extra[-_]index[-_]url", content)


class TestCheckAwsTokenValidity:
    """Tests for '_check_aws_token_validity', which resolves/refreshes the
    AWS CodeArtifact token and repopulates 'python.index_url' and
    'python.extra_index_urls' accordingly. The CodeArtifact base URL (which
    carries the auth token as its password) is cached in the aws_auth memo
    itself, alongside the timestamp, so the cached-token path never touches
    the venv's pip configuration file."""

    @staticmethod
    def _make_cfg(tmp_path, extra_indexes=(), existing_extra_index_urls=()):
        """Build a MagicMock cfg suitable for _check_aws_token_validity."""
        cfg = mock.MagicMock()
        cfg.python.aws_auth.memo = str(tmp_path / "aws_auth.memo")
        cfg.python.aws_auth.key_duration = 3600
        cfg.python.aws_auth.static_oidc = False
        cfg.python.aws_auth.client_secret = ""
        cfg.python.aws_auth.client_id = None
        cfg.python.aws_auth.role_arn = None
        cfg.python.aws_auth.index = "16.0/simple"
        cfg.python.aws_auth.extra_indexes = list(extra_indexes)
        cfg.python.extra_index_urls = list(existing_extra_index_urls)
        # venv doesn't exist, so _configure_pipconf won't be triggered.
        cfg.python.venv = str(tmp_path / "venv")
        return cfg

    @staticmethod
    def _seed_token_cache(tmp_path, index_base_url, age_seconds=0):
        """
        Write an 'aws_auth.memo' holding `index_base_url` at an age of
        `age_seconds`, so '_check_aws_token_validity' takes the cached-token
        branch (age_seconds=0) or the expired-token branch.
        """
        import pickle
        import time

        memo_path = tmp_path / "aws_auth.memo"
        timestamp = int(time.time()) - age_seconds
        memo_path.write_bytes(
            pickle.dumps([("aws_auth_timestamp", timestamp, index_base_url)])
        )

    @pytest.mark.parametrize(
        "extra_indexes,existing_extra_index_urls,expected_extra_index_urls",
        (
            pytest.param(
                ["stb/simple"],
                [],
                [
                    "https://aws:TOKEN@contact-123.d.codeartifact.eu-central-1"
                    ".amazonaws.com/pypi/stb/simple"
                ],
                id="resolves_extra_indexes",
            ),
            pytest.param(
                ["stb/simple"],
                ["https://gitlab.example/simple"],
                [
                    "https://gitlab.example/simple",
                    "https://aws:TOKEN@contact-123.d.codeartifact.eu-central-1"
                    ".amazonaws.com/pypi/stb/simple",
                ],
                id="merges_with_existing",
            ),
            pytest.param([], [], [], id="without_extra_indexes"),
        ),
    )
    @mock.patch("csspin_python.python.info")
    @mock.patch("csaccess.get_ca_pypi_url_programmatic")
    def test_resolves_extra_indexes(
        self,
        mock_get_url,
        _mock_info,
        tmp_path,
        extra_indexes,
        existing_extra_index_urls,
        expected_extra_index_urls,
    ):
        """
        Test that a fresh CodeArtifact token resolves 'python.index_url' and
        merges 'aws_auth.extra_indexes' into 'python.extra_index_urls' on
        top of (not overwriting) any pre-existing entries.
        """
        mock_get_url.return_value = (
            "https://aws:TOKEN@contact-123.d.codeartifact.eu-central-1"
            ".amazonaws.com/pypi"
        )
        cfg = self._make_cfg(
            tmp_path,
            extra_indexes=extra_indexes,
            existing_extra_index_urls=existing_extra_index_urls,
        )

        _check_aws_token_validity(cfg)

        assert cfg.python.index_url == (
            "https://aws:TOKEN@contact-123.d.codeartifact.eu-central-1"
            ".amazonaws.com/pypi/16.0/simple"
        )
        assert cfg.python.extra_index_urls == expected_extra_index_urls

    @pytest.mark.parametrize(
        "existing_extra_index_urls,expected_extra_index_urls",
        (
            pytest.param(
                [],
                ["https://aws:TOKEN@host/pypi/stb/simple"],
                id="cached_only",
            ),
            pytest.param(
                ["https://gitlab.example/simple"],
                [
                    "https://gitlab.example/simple",
                    "https://aws:TOKEN@host/pypi/stb/simple",
                ],
                id="merges_with_existing",
            ),
        ),
    )
    @mock.patch("csaccess.get_ca_pypi_url_programmatic")
    @mock.patch("csspin_python.python.info")
    def test_uses_cached_token(
        self,
        _mock_info,
        mock_get_url,
        tmp_path,
        existing_extra_index_urls,
        expected_extra_index_urls,
    ):
        """
        Test that a cached (non-expired) token resolves 'python.index_url'
        and 'python.extra_index_urls' from the CodeArtifact base URL stored
        in the aws_auth memo, without contacting AWS again, merging with any
        pre-existing entries.
        """
        self._seed_token_cache(tmp_path, "https://aws:TOKEN@host/pypi")
        cfg = self._make_cfg(
            tmp_path,
            extra_indexes=["stb/simple"],
            existing_extra_index_urls=existing_extra_index_urls,
        )

        _check_aws_token_validity(cfg)

        assert cfg.python.index_url == "https://aws:TOKEN@host/pypi/16.0/simple"
        assert cfg.python.extra_index_urls == expected_extra_index_urls
        mock_get_url.assert_not_called()

    @mock.patch("csaccess.get_ca_pypi_url_programmatic")
    @mock.patch("csspin_python.python.info")
    def test_refetches_when_token_expired(self, _mock_info, mock_get_url, tmp_path):
        """
        Test that an expired memo entry is discarded and a fresh token is
        fetched from AWS instead of being reused.
        """
        self._seed_token_cache(
            tmp_path, "https://aws:OLD@host/pypi", age_seconds=999_999
        )
        mock_get_url.return_value = (
            "https://aws:TOKEN@contact-123.d.codeartifact.eu-central-1"
            ".amazonaws.com/pypi"
        )
        cfg = self._make_cfg(tmp_path, extra_indexes=["stb/simple"])

        _check_aws_token_validity(cfg)

        mock_get_url.assert_called_once()
        assert cfg.python.index_url == (
            "https://aws:TOKEN@contact-123.d.codeartifact.eu-central-1"
            ".amazonaws.com/pypi/16.0/simple"
        )


class TestWheel:
    """Tests for the 'python:wheel' task's index/extra-index propagation."""

    @mock.patch("csspin_python.python.setenv")
    def test_sets_extra_index_url_when_configured(self, mock_setenv):
        """PIP_EXTRA_INDEX_URL is set when extra indexes are configured."""
        cfg = mock.MagicMock()
        cfg.python.index_url = "https://index.example/simple"
        cfg.python.extra_index_urls = ["https://index.example/stb/simple"]
        cfg.python.build_wheels = []

        wheel(cfg, paths=())

        mock_setenv.assert_any_call(PIP_INDEX_URL="https://index.example/simple")
        mock_setenv.assert_any_call(
            PIP_EXTRA_INDEX_URL="https://index.example/stb/simple"
        )

    @mock.patch("csspin_python.python.setenv")
    def test_does_not_set_extra_index_url_when_none_configured(self, mock_setenv):
        """PIP_EXTRA_INDEX_URL is left untouched when there are no extras."""
        cfg = mock.MagicMock()
        cfg.python.index_url = "https://index.example/simple"
        cfg.python.extra_index_urls = []
        cfg.python.build_wheels = []

        wheel(cfg, paths=())

        calls = [call.kwargs for call in mock_setenv.call_args_list]
        assert not any("PIP_EXTRA_INDEX_URL" in kwargs for kwargs in calls)


class TestObfuscateIndexUrl:
    """Tests for '_obfuscate_index_url', which must tolerate any URL shape
    reachable via '_check_aws_token_validity''s cached branch, not only
    CodeArtifact's 'user:token@host' shape."""

    @pytest.fixture(autouse=True)
    def clean_secrets(self):
        """Isolate 'csspin.secrets' (a process-global set) for each test."""
        from csspin import secrets

        original = set(secrets)
        secrets.clear()
        yield secrets
        secrets.clear()
        secrets.update(original)

    @pytest.mark.parametrize(
        "url,expected_secrets",
        (
            pytest.param(
                "https://aws:TOKEN@host/pypi/16.0/simple",
                {"TOKEN"},
                id="credentialed_url",
            ),
            pytest.param("https://gitlab.example/simple", set(), id="no_credentials"),
            pytest.param(
                "http://mirror.internal:8080/simple",
                set(),
                id="port_but_no_credentials",
            ),
            pytest.param("https://aws:@host/pypi/simple", set(), id="empty_password"),
        ),
    )
    def test_registers_only_a_genuine_password(
        self, clean_secrets, url, expected_secrets
    ):
        """Only a URL with a non-empty password registers a secret; anything
        else (no credentials, a port mistaken for one, an empty password) is
        a no-op instead of crashing or leaking a bogus value."""
        _obfuscate_index_url(url)

        assert clean_secrets == expected_secrets


class TestGetProjectMetadata:
    """
    Tests for 'get_project_metadata', which must expose configured extra
    indexes to the isolated 'python -m build --metadata' subprocess the same
    way 'python:wheel' does, so packages required only by
    '[build-system].requires' (e.g. from an aws_auth extra CodeArtifact
    index) can be found too.
    """

    @mock.patch("csspin_python.python.CONFIG")
    @mock.patch("csspin_python.python.backtick")
    @mock.patch("csspin_python.python.setenv")
    def test_sets_and_unsets_extra_index_url(
        self, mock_setenv, mock_backtick, mock_config
    ):
        """PIP_EXTRA_INDEX_URL is set around the build call and unset after."""
        mock_config.verbosity = Verbosity.NORMAL
        mock_backtick.return_value = '{"name": "foo", "version": "1.0"}'

        get_project_metadata(
            "/tmp/project-with-extras",
            "https://index.example/simple",
            extra_index_urls=("https://index.example/stb/simple",),
        )

        mock_setenv.assert_any_call(PIP_INDEX_URL="https://index.example/simple")
        mock_setenv.assert_any_call(
            PIP_EXTRA_INDEX_URL="https://index.example/stb/simple"
        )
        mock_setenv.assert_any_call(PIP_EXTRA_INDEX_URL=None)
        mock_setenv.assert_any_call(PIP_INDEX_URL=None)

    @mock.patch("csspin_python.python.CONFIG")
    @mock.patch("csspin_python.python.backtick")
    @mock.patch("csspin_python.python.setenv")
    def test_does_not_touch_extra_index_url_when_none_configured(
        self, mock_setenv, mock_backtick, mock_config
    ):
        """PIP_EXTRA_INDEX_URL is left untouched when there are no extras."""
        mock_config.verbosity = Verbosity.NORMAL
        mock_backtick.return_value = '{"name": "foo", "version": "1.0"}'

        get_project_metadata(
            "/tmp/project-without-extras", "https://index.example/simple"
        )

        calls = [call.kwargs for call in mock_setenv.call_args_list]
        assert not any("PIP_EXTRA_INDEX_URL" in kwargs for kwargs in calls)


@pytest.mark.parametrize(
    "requirement, expected_filename, context",
    (
        ("-r requirements.txt", "requirements.txt", nullcontext()),
        ("-r=foo.txt", "foo.txt", nullcontext()),
        ("-r    bar.txt", "bar.txt", nullcontext()),
        ("-rbaz.txt", "baz.txt", nullcontext()),
        ("--requirement requirements.txt", "requirements.txt", nullcontext()),
        ("--requirement=foo.txt", "foo.txt", nullcontext()),
        ("--requirement    bar.txt", "bar.txt", nullcontext()),
        ("-c constraint.txt", "constraint.txt", nullcontext()),
        ("-c=foo.txt", "foo.txt", nullcontext()),
        ("-c    bar.txt", "bar.txt", nullcontext()),
        ("-cbaz.txt", "baz.txt", nullcontext()),
        ("--constraint constraint.txt", "constraint.txt", nullcontext()),
        ("--constraint=foo.txt", "foo.txt", nullcontext()),
        ("--constraint    bar.txt", "bar.txt", nullcontext()),
        ("--requirementrequirements.txt", "requirements.txt", pytest.raises(Abort)),
        ("--constraint", "constraint.txt", pytest.raises(Abort)),
    ),
)
def test__split_requirement_option(tmp_path, requirement, expected_filename, context):
    """
    Test whether _split_requirement_option works correctly.
    """
    expected_file = tmp_path / expected_filename
    expected_file.touch()
    with context:
        assert (
            _split_requirement_option(requirement, tmp_path)
            == tmp_path / expected_filename
        )


@pytest.mark.parametrize(
    "exists_return, check_output_side_effect, use, "
    "version, expected_result, expect_warn, description",
    [
        # no `use`, version matches prefix -> True
        (
            True,
            [b"Python 3.11.4"],
            None,
            "3.11",
            True,
            False,
            "version matches",
        ),
        # no `use`, version does not match prefix -> False
        (
            True,
            [b"Python 3.10.2"],
            None,
            "3.11",
            False,
            False,
            "version mismatch",
        ),
        # no `use`, empty version string -> False
        (
            True,
            [b"Python "],
            None,
            "3.11",
            False,
            False,
            "empty version output",
        ),
        # `use` set, versions match -> True, no warning
        (
            True,
            [b"Python 3.11.4", b"Python 3.11.4"],
            "/usr/bin/python3.11",
            "3.11",
            True,
            False,
            "use matches venv",
        ),
        # `use` set, versions differ -> True but warning emitted
        (
            True,
            [b"Python 3.11.4", b"Python 3.12.0"],
            "/usr/bin/python3.12",
            "3.11",
            True,
            True,
            "use differs but still healthy",
        ),
        # venv exists but neither version nor use is set -> False
        (
            True,
            [b"Python 3.11.4"],
            None,
            None,
            False,
            False,
            "no version or use configured",
        ),
        # venv exists, use is set but version is not -> True if use matches
        (
            True,
            [b"Python 3.11.4", b"Python 3.11.4"],
            "/usr/bin/python3.11",
            None,
            True,
            False,
            "only use set, matches",
        ),
        # venv exists, use is set but version is not ->
        # True even if use differs (with warning)
        (
            True,
            [b"Python 3.11.4", b"Python 3.12.0"],
            "/usr/bin/python3.12",
            None,
            True,
            True,
            "only use set, differs",
        ),
        # empty string version (edge case)
        (
            True,
            [b"Python 3.11.4"],
            None,
            "",
            False,
            False,
            "empty version string config",
        ),
        # python executable exists but fails to run -> should return False
        (
            True,
            CalledProcessError(1, "python"),
            None,
            "3.11",
            False,
            False,
            "python execution fails",
        ),
        # use is set but points to non-existent executable -> should return False
        (
            True,
            [b"Python 3.11.4", CalledProcessError(1, "python")],
            "/usr/bin/nonexistent",
            "3.11",
            False,
            False,
            "use executable missing",
        ),
    ],
    ids=[
        "version_matches_prefix",
        "version_no_match",
        "empty_version_string",
        "use_versions_match",
        "use_versions_differ_warns",
        "neither_version_nor_use_set",
        "only_use_set_matches",
        "only_use_set_differs",
        "empty_version_config",
        "python_execution_fails",
        "use_executable_missing",
    ],
)
@mock.patch("csspin_python.python.warn")
@mock.patch("csspin_python.python.check_output")
@mock.patch("csspin_python.python.exists")
def test_check_venv(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    mock_exists,
    mock_check_output,
    mock_warn,
    exists_return,
    check_output_side_effect,
    use,
    version,
    expected_result,
    expect_warn,
    description,
):
    """
    Tests the check_venv function for all its cases.
    """
    mock_exists.return_value = exists_return

    # Handle both list of outputs and direct exception
    if isinstance(check_output_side_effect, CalledProcessError):
        mock_check_output.side_effect = check_output_side_effect
    else:
        mock_check_output.side_effect = check_output_side_effect

    cfg = mock.MagicMock()
    cfg.python.python = "venv/bin/python"
    cfg.python.use = use
    cfg.python.version = version

    result = _check_venv(cfg)
    assert result == expected_result, f"Failed: {description}"

    if expect_warn:
        mock_warn.assert_called_once()
        assert "does not match" in mock_warn.call_args[0][0]
    else:
        mock_warn.assert_not_called()


@mock.patch("csspin_python.python.exists", return_value=True)
@mock.patch("csspin_python.python.echo")
@mock.patch("csspin_python.python.venv_init")
def test_python_env_nesting(mock_venv_init, _mock_echo, _mock_exists):
    """
    Nesting python_env() must not corrupt the outer activation or lose the
    original environment on teardown.

    csspin.sh activates spin.subprocess_environment (i.e. python_env) around the
    commands it spawns, so an explicit ``with python_env(cfg):`` block that calls
    sh() ends up nesting python_env. This must be safe.

    `exists` is patched True so python_env takes the activation path (the venv is
    considered provisioned) rather than its no-op path.

    The inner activation sets *different* values for the same variables, so the
    test also pins down which value wins where: the inner value inside the inner
    context, and the outer value again once the inner context exits.

    Sequence:
      original env  -> [outer enters w/ "outer"] -> var == "outer"
                    -> [inner enters w/ "inner"] -> var == "inner"
                    -> [inner exits]             -> var == "outer" (outer intact)
                    -> [outer exits]             -> var gone (original restored)
    """
    cfg = mock.MagicMock()

    var = "_SPIN_PYTHON_ENV_TEST"
    inner_only = "_SPIN_PYTHON_ENV_INNER_ONLY"

    original_env = os.environ.copy()
    original_sys_path = sys.path.copy()
    original_sys_prefix = sys.prefix

    # Patch EXPORTS to a list we grow in place between the two activations.
    # EXPORTS is read on each python_env() entry and applied in order, so the
    # outer activation applies "outer" and the inner one -- after extending
    # EXPORTS -- applies a later "inner" (plus an inner-only variable) that wins.
    exports = [(var, "outer")]
    with mock.patch("csspin_python.python.EXPORTS", exports):
        with python_env(cfg):
            assert os.environ[var] == "outer"
            assert inner_only not in os.environ

            # Extend (not replace) EXPORTS for the inner activation; the later
            # entry overrides the earlier "outer" value.
            exports.extend([(var, "inner"), (inner_only, "1")])
            with python_env(cfg):
                # Inner value wins inside the inner context.
                assert os.environ[var] == "inner"
                assert os.environ[inner_only] == "1"

            # Inner exit restores the value present when the inner context was
            # entered (the outer activation), and drops the inner-only variable.
            assert os.environ[var] == "outer"
            assert inner_only not in os.environ

        # Outer exit restores the process to its original state.
        assert var not in os.environ
        assert os.environ == original_env
        assert sys.path == original_sys_path
        assert sys.prefix == original_sys_prefix

    assert mock_venv_init.call_count == 2
