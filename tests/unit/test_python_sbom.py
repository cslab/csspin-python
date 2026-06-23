# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2026 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the unit tests for the python_sbom plugin"""

from unittest import mock

import pytest
from click import Abort

# Mock `csspin.task` away as the import fails otherwise
with mock.patch("csspin.task"):
    from csspin_python.python_sbom import (
        _build_primary_component,
        _parse_authors,
    )


_AUTHOR_METADATA = {
    "name": "cs.foo",
    "version": "1.2.3",
    "license": "Apache-2.0",
    "author": "CONTACT Software GmbH",
    "author_email": "CONTACT Software GmbH <ptm-team@contact-software.com>",
}


class TestParseAuthors:
    """Tests for _parse_authors."""

    def test_rfc2822_name_in_email_field(self):
        """Extracts name+address from a 'Name <email>' string"""
        result = _parse_authors(
            author_name="",
            author_email="CONTACT Software GmbH <ptm-team@contact-software.com>",
        )
        assert result == "CONTACT Software GmbH (ptm-team@contact-software.com)"

    def test_falls_back_to_author_name(self):
        """Uses author_name when the email field has no display name"""
        result = _parse_authors(
            author_name="CONTACT Software GmbH",
            author_email="ptm-team@contact-software.com",
        )
        assert result == "CONTACT Software GmbH (ptm-team@contact-software.com)"

    def test_multiple_entries(self):
        """Joins multiple RFC 2822 entries with ', '"""
        result = _parse_authors(
            author_name="",
            author_email="Alice <alice@example.com>, Bob <bob@example.com>",
        )
        assert result == "Alice (alice@example.com), Bob (bob@example.com)"

    def test_missing_email_aborts(self):
        """Calls die when author_email is empty"""
        with pytest.raises(Abort):
            _parse_authors(author_name="Someone", author_email="")

    def test_entry_missing_name_aborts(self):
        """Calls die when an entry has no display name"""
        with pytest.raises(Abort):
            _parse_authors(author_name="", author_email="ptm-team@contact-software.com")


class TestBuildPrimaryComponent:
    """Tests for _build_primary_component."""

    def test_returns_component_and_ref(self):
        """Returns the component dict and primary_ref"""
        component, ref = _build_primary_component(_AUTHOR_METADATA)

        assert ref == "cs.foo==1.2.3"
        assert component == {
            "author": "CONTACT Software GmbH (ptm-team@contact-software.com)",
            "bom-ref": "cs.foo==1.2.3",
            "licenses": [{"expression": "Apache-2.0"}],
            "name": "cs.foo",
            "type": "application",
            "version": "1.2.3",
        }

    def test_no_purl(self):
        """Never includes a purl field"""
        component, _ = _build_primary_component(_AUTHOR_METADATA)
        assert "purl" not in component

    @pytest.mark.parametrize("missing_key", ["name", "version", "license"])
    def test_missing_required_field_aborts(self, missing_key):
        """Calls die when a required metadata field is absent"""
        metadata = {**_AUTHOR_METADATA, missing_key: ""}
        with pytest.raises(Abort):
            _build_primary_component(metadata)
