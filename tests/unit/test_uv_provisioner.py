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
    from csspin_python.uv_provisioner import _update_index_url_in_toml


def test__update_index_url_in_toml_updates_existing_file(tmp_path):
    """Ensure _update_index_url_in_toml rewrites index-url when it changed."""
    uv_toml_path = tmp_path / "uv.toml"
    uv_toml_path.write_text(
        'index-url = "https://old.example/simple"\nprerelease = "if-necessary-or-explicit"',
        encoding="utf-8",
    )

    cfg = mock.MagicMock()
    cfg.uv_provisioner.uv_toml_path = str(uv_toml_path)
    cfg.python.index_url = "https://new.example/simple"

    _update_index_url_in_toml(cfg)

    assert tomllib.loads(uv_toml_path.read_text(encoding="utf-8")) == {
        "index-url": "https://new.example/simple",
        "prerelease": "if-necessary-or-explicit",
    }
