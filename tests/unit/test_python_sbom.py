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
        _build_purl,
        _parse_authors,
    )


_AUTHOR_METADATA = {
    "name": "cs.foo",
    "version": "1.2.3",
    "license": "Apache-2.0",
    "author": "CONTACT Software GmbH",
    "author_email": "CONTACT Software GmbH <ptm-team@contact-software.com>",
}
_FILE_NAME = "cs_foo-1.2.3-py3-none-any.whl"


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


class TestPrimaryComponentMetadata:
    """
    Tests ensuring checking for proper generation of SBOM metadata for the
    primary component.
    """

    def test_returns_component_and_ref(self):
        """Ensure it returns the component dict and primary_ref"""
        component, ref = _build_primary_component(
            _AUTHOR_METADATA,
            "https://packages.contact.de/apps/2026.2/+simple/",
            _FILE_NAME,
        )

        assert ref == "cs.foo==1.2.3"
        assert component == {
            "author": "CONTACT Software GmbH (ptm-team@contact-software.com)",
            "bom-ref": "cs.foo==1.2.3",
            "licenses": [{"expression": "Apache-2.0"}],
            "name": "cs.foo",
            "purl": (
                "pkg:pypi/cs-foo@1.2.3?file_name=cs_foo-1.2.3-py3-none-any.whl"
                "&repository_url=https:%2F%2Fpackages.contact.de%2Fapps%2F2026.2"
            ),
            "type": "application",
            "version": "1.2.3",
        }

    def test_purl_normalizes_name_per_pep503(self):
        """Ensure it normalizes the project name into the purl per PEP 503"""
        purl = _build_purl(
            _AUTHOR_METADATA["name"],
            _AUTHOR_METADATA["version"],
            "https://packages.contact.de/apps/2026.2/+simple/",
            _FILE_NAME,
        )
        assert purl == (
            "pkg:pypi/cs-foo@1.2.3?file_name=cs_foo-1.2.3-py3-none-any.whl"
            "&repository_url=https:%2F%2Fpackages.contact.de%2Fapps%2F2026.2"
        )

    def test_purl_omits_repository_url_for_public_pypi(self):
        """Ensure to omit the repository_url qualifier when published to pypi.org"""
        purl = _build_purl(
            _AUTHOR_METADATA["name"],
            _AUTHOR_METADATA["version"],
            "https://pypi.org/simple",
            _FILE_NAME,
        )
        assert purl == ("pkg:pypi/cs-foo@1.2.3?file_name=cs_foo-1.2.3-py3-none-any.whl")

    def test_purl_strips_credentials_from_index_url(self):
        """Never leaks basic-auth credentials (e.g. a CodeArtifact token) into the purl"""
        purl = _build_purl(
            _AUTHOR_METADATA["name"],
            _AUTHOR_METADATA["version"],
            "https://aws:abcSECRETtoken@my-domain-12345.d.codeartifact."
            "eu-central-1.amazonaws.com/pypi/my-repo/simple/",
            _FILE_NAME,
        )
        assert purl == (
            "pkg:pypi/cs-foo@1.2.3?file_name=cs_foo-1.2.3-py3-none-any.whl"
            "&repository_url=https:%2F%2Fmy-domain-12345.d."
            "codeartifact.eu-central-1.amazonaws.com%2Fpypi%2Fmy-repo"
        )

    @pytest.mark.parametrize(
        ("index_url", "expected"),
        [
            (
                "https://packages.contact.de/apps/2026.2-dev/+simple/",
                "https:%2F%2Fpackages.contact.de%2Fapps%2F2026.2-dev",
            ),
            (
                "https://packages.contact.de/apps/2026.2-dev/+simple",
                "https:%2F%2Fpackages.contact.de%2Fapps%2F2026.2-dev",
            ),
            (
                "https://packages.contact.de/apps/2026.2-dev/",
                "https:%2F%2Fpackages.contact.de%2Fapps%2F2026.2-dev",
            ),
        ],
    )
    def test_purl_drops_the_index_endpoint_from_repository_url(
        self, index_url, expected
    ):
        """Reduces a index URL to the repository base URL"""
        purl = _build_purl(
            _AUTHOR_METADATA["name"], _AUTHOR_METADATA["version"], index_url, _FILE_NAME
        )
        assert purl == (
            f"pkg:pypi/cs-foo@1.2.3?file_name={_FILE_NAME}"
            f"&repository_url={expected}"
        )

    def test_purl_sorts_qualifiers_by_key(self):
        """Orders the qualifiers alphabetically, as the canonical purl requires"""
        purl = _build_purl(
            _AUTHOR_METADATA["name"],
            _AUTHOR_METADATA["version"],
            "https://packages.contact.de/apps/2026.2/+simple/",
            "foo.whl",
        )
        assert purl == (
            "pkg:pypi/cs-foo@1.2.3?file_name=foo.whl"
            "&repository_url=https:%2F%2Fpackages.contact.de%2Fapps%2F2026.2"
        )

    def test_purl_keeps_colons_unencoded_in_qualifier_values(self):
        """Leaves a colon literal"""
        purl = _build_purl(
            _AUTHOR_METADATA["name"],
            _AUTHOR_METADATA["version"],
            "http://localhost:3141/root/pypi/+simple/",
            _FILE_NAME,
        )
        assert purl == (
            "pkg:pypi/cs-foo@1.2.3?file_name=cs_foo-1.2.3-py3-none-any.whl"
            "&repository_url=http:%2F%2Flocalhost:3141%2Froot%2Fpypi"
        )

    def test_purl_percent_encodes_the_version(self):
        """Percent-encodes a PEP 440 local version label in the purl version"""
        purl = _build_purl(
            _AUTHOR_METADATA["name"],
            "1.2.3+g1a2b3c4",
            "https://pypi.org/simple",
            "cs_foo-1.2.3_g1a2b3c4-py3-none-any.whl",
        )
        assert purl == (
            "pkg:pypi/cs-foo@1.2.3%2Bg1a2b3c4"
            "?file_name=cs_foo-1.2.3_g1a2b3c4-py3-none-any.whl"
        )

    @pytest.mark.parametrize("missing_key", ["name", "version", "license"])
    def test_missing_required_field_aborts(self, missing_key):
        """Calls die when a required metadata field is absent"""
        metadata = {**_AUTHOR_METADATA, missing_key: ""}
        with pytest.raises(Abort):
            _build_primary_component(metadata, "https://pypi.org/simple", _FILE_NAME)
