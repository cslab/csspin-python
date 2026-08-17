# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2026 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing unit tests for csspin_python.uv_provisioner."""

from unittest import mock

try:
    import tomllib
except ImportError:
    import tomli as tomllib

# # Mock `csspin.task` away as the import fails otherwise
with mock.patch("csspin.task"):
    from csspin_python.uv_provisioner import (
        _configure_uv_toml,
        _update_index_url_in_toml,
    )


def test__update_index_url_in_toml_updates_existing_file(tmp_path):
    """Ensure _update_index_url_in_toml rewrites index-url when it changed."""
    uv_toml_path = tmp_path / "uv.toml"
    uv_toml_path.write_text(
        'index-url = "https://old.example/simple"\nprerelease = "if-necessary-or-explicit"',
        encoding="utf-8",
    )

    cfg = mock.MagicMock()
    cfg.uv_provisioner.uv_toml = ""
    cfg.uv_provisioner.uv_toml_path = str(uv_toml_path)
    cfg.python.index_url = "https://new.example/simple"
    cfg.python.extra_index_urls = []

    _update_index_url_in_toml(cfg)

    assert tomllib.loads(uv_toml_path.read_text(encoding="utf-8")) == {
        "index-url": "https://new.example/simple",
        "prerelease": "if-necessary-or-explicit",
    }


def test_updates_extra_index_urls(tmp_path):
    """Ensure _update_index_url_in_toml rewrites extra-index-url when it changed."""
    uv_toml_path = tmp_path / "uv.toml"
    uv_toml_path.write_text(
        'index-url = "https://old.example/simple"\n',
        encoding="utf-8",
    )

    cfg = mock.MagicMock()
    cfg.uv_provisioner.uv_toml = ""
    cfg.uv_provisioner.uv_toml_path = str(uv_toml_path)
    cfg.python.index_url = "https://old.example/simple"
    cfg.python.extra_index_urls = ["https://index.example/stb/simple"]

    _update_index_url_in_toml(cfg)

    written = tomllib.loads(uv_toml_path.read_text(encoding="utf-8"))
    assert written["index-url"] == "https://old.example/simple"
    assert written["extra-index-url"] == ["https://index.example/stb/simple"]


def test_clears_stale_extra_index_urls(tmp_path):
    """
    Regression test: when 'python.extra_index_urls' becomes empty (e.g. an
    'aws_auth.extra_indexes' entry was removed), the stale 'extra-index-url'
    entry must be removed from uv.toml too, not left with a dead token that
    would make uv hard-fail on every install.
    """

    uv_toml_path = tmp_path / "uv.toml"
    uv_toml_path.write_text(
        'index-url = "https://old.example/simple"\n'
        'extra-index-url = ["https://old.example/stb/simple"]\n',
        encoding="utf-8",
    )

    cfg = mock.MagicMock()
    cfg.uv_provisioner.uv_toml = ""
    cfg.uv_provisioner.uv_toml_path = str(uv_toml_path)
    cfg.python.index_url = "https://old.example/simple"
    cfg.python.extra_index_urls = []

    _update_index_url_in_toml(cfg)

    assert tomllib.loads(uv_toml_path.read_text(encoding="utf-8")) == {
        "index-url": "https://old.example/simple",
    }


def test_no_op_when_nothing_changed(tmp_path):
    """
    Guard against reintroducing a rewrite-every-run regression: if
    'index-url' matches and there are no extra index urls on either side, the
    file must not be rewritten.
    """
    uv_toml_path = tmp_path / "uv.toml"
    original_content = 'index-url = "https://old.example/simple"\n'
    uv_toml_path.write_text(original_content, encoding="utf-8")
    mtime_before = uv_toml_path.stat().st_mtime_ns

    cfg = mock.MagicMock()
    cfg.uv_provisioner.uv_toml = ""
    cfg.uv_provisioner.uv_toml_path = str(uv_toml_path)
    cfg.python.index_url = "https://old.example/simple"
    cfg.python.extra_index_urls = []

    _update_index_url_in_toml(cfg)

    assert uv_toml_path.stat().st_mtime_ns == mtime_before


def test_drops_template_extra_index_url_on_refresh(tmp_path):
    """
    Regression test: a template-declared 'extra-index-url' must not survive
    a token refresh. 'python.extra_index_urls' is the only supported way to
    configure extra indexes, so the on-disk file must end up with exactly
    the resolved 'python.extra_index_urls', not a mix.
    """
    uv_toml_path = tmp_path / "uv.toml"
    uv_toml_path.write_text(
        'index-url = "https://aws:OLDTOKEN@host/pypi/16.0/simple"\n'
        'extra-index-url = ["https://gitlab.example/simple", '
        '"https://aws:OLDTOKEN@host/pypi/stb/simple"]\n',
        encoding="utf-8",
    )

    cfg = mock.MagicMock()
    cfg.uv_provisioner.uv_toml = 'extra-index-url = ["https://gitlab.example/simple"]'
    cfg.uv_provisioner.uv_toml_path = str(uv_toml_path)
    cfg.python.index_url = "https://aws:NEWTOKEN@host/pypi/16.0/simple"
    cfg.python.extra_index_urls = ["https://aws:NEWTOKEN@host/pypi/stb/simple"]

    _update_index_url_in_toml(cfg)

    written = tomllib.loads(uv_toml_path.read_text(encoding="utf-8"))
    assert written["index-url"] == "https://aws:NEWTOKEN@host/pypi/16.0/simple"
    assert written["extra-index-url"] == ["https://aws:NEWTOKEN@host/pypi/stb/simple"]


def test_writes_extra_index_urls(tmp_path):
    """Ensure _configure_uv_toml writes extra-index-url alongside index-url."""
    uv_toml_path = tmp_path / "uv.toml"

    cfg = mock.MagicMock()
    cfg.uv_provisioner.uv_toml = ""
    cfg.uv_provisioner.uv_toml_path = str(uv_toml_path)
    cfg.python.index_url = "https://example.com/simple"
    cfg.python.extra_index_urls = ["https://example.com/stb/simple"]

    _configure_uv_toml(cfg)

    assert tomllib.loads(uv_toml_path.read_text(encoding="utf-8")) == {
        "index-url": "https://example.com/simple",
        "extra-index-url": ["https://example.com/stb/simple"],
    }


def test_ignores_template_index_url_and_extra_index_url(tmp_path):
    """
    Regression test: 'index-url'/'extra-index-url' declared in the
    spinfile-configured 'uv_provisioner.uv_toml' template must be ignored.
    'python.index_url'/'python.extra_index_urls' are the only supported way
    to configure these, mirroring 'python.pipconf'.
    """
    uv_toml_path = tmp_path / "uv.toml"

    cfg = mock.MagicMock()
    cfg.uv_provisioner.uv_toml = (
        'index-url = "https://template.example/simple"\n'
        'extra-index-url = ["https://template.example/stb/simple"]\n'
    )
    cfg.uv_provisioner.uv_toml_path = str(uv_toml_path)
    cfg.python.index_url = "https://example.com/simple"
    cfg.python.extra_index_urls = ["https://example.com/stb/simple"]

    _configure_uv_toml(cfg)

    assert tomllib.loads(uv_toml_path.read_text(encoding="utf-8")) == {
        "index-url": "https://example.com/simple",
        "extra-index-url": ["https://example.com/stb/simple"],
    }
