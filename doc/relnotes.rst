.. -*- coding: utf-8 -*-
   Copyright (C) 2025 CONTACT Software GmbH
   https://www.contact-software.com/

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

.. This document contains the release notes for csspin-python. Each release is
   documented in a separate section, starting with the most recent release at
   the top.

   The release section must be renamed to the actual release tag with a prefixed
   "v". The date of the release must be in the format `Month Day, Year`/`"%B %d,
   %Y"`.

    At least one of these subsections must be present for each release:

    - Enhancements
    - Bug Fixes
    - Chores

    Each of these subsection must contain a bulleted list of changes made in the
    release. Each bullet must contain a short description of the change and a
    reference to the issue or merge request where the change was made.

    If required, the additional subsections can be added:

    - Breaking Changes
    - Migration Guide

    These additional subsections must contain a concise description of the
    changes required to migrate from the previous version to the new version.
    This may include code examples, configuration changes, or other relevant
    information to assist users in updating their implementations.

    Example:

    v2.0.2
    ======

    December 10, 2025

    Chores
    ------

    - Add release notes to the documentation structure (`#100 <https://code.contact.de/pod/components/csspin/-/issues/100>`_)


=============
Release Notes
=============

v6.0.0
======

August 18, 2026

Breaking Changes
----------------

- ``python.aws_auth.static_oidc`` and ``python.aws_auth.client_secret`` are
  removed. csaccess selects the AWS CodeArtifact authentication mode now, so
  ``csspin-python`` neither forwards these options nor reads
  ``CS_AWS_OIDC_CLIENT_SECRET`` (`#128
  <https://code.contact.de/pod/components/csspin-python/-/work_items/128>`_)
- ``python.aws_auth.index`` no longer defaults to ``16.0/simple``. Projects
  using ``aws_auth`` must set the CodeArtifact repository index explicitly
  (`#130
  <https://code.contact.de/pod/components/csspin-python/-/work_items/130>`_)
- ``csaccess>=3.0.0`` is now the default when ``aws_auth`` is enabled.

Migration Guide
---------------

- Drop ``static_oidc`` and ``client_secret`` from the ``python.aws_auth``
  section of the project's ``spinfile.yaml``. The `csaccess package
  description <https://pypi.org/project/csaccess/>`_ documents the available
  authentication modes and the environment they require.
- Set ``python.aws_auth.index`` if the project relied on the previous default,
  for example:

  .. code-block:: yaml

      python:
          aws_auth:
              enabled: True
              index: 2026.2/simple

Enhancements
------------

- Support csaccess GitLab CI OIDC authentication mode (`#128
  <https://code.contact.de/pod/components/csspin-python/-/work_items/128>`_)
- Support ``extra_indexes`` for ``aws_auth`` (`#129
  <https://code.contact.de/pod/components/csspin-python/-/work_items/129>`_)

Bug Fixes
---------

- python: ``aws_auth`` stack does not verify value of ``index_url`` in
  ``pip.conf`` (`#131
  <https://code.contact.de/pod/components/csspin-python/-/work_items/131>`_)

v5.0.0
======

August 11, 2026

Breaking Changes
----------------

- ``csspin-python`` no longer globally activates the venv in the
  ``python`` plugin's ``init`` hook. It now registers ``python_env()``
  as spin's ``subprocess_environment``, so the venv is activated on
  demand for ``spin run``, ``extra_tasks``, and provisioning (`!109
  <https://code.contact.de/pod/components/csspin-python/-/merge_requests/109>`_)

Migration Guide
---------------

- This release requires ``csspin>=3.1.1``.

Enhancements
------------

- Add a ``purl`` field to the primary component of generated Python
  SBOMs (`!121
  <https://code.contact.de/pod/components/csspin-python/-/merge_requests/121>`_)

Chores
------

- Update CI includes and stale references after the move to
  ``pod/components`` (`!122
  <https://code.contact.de/pod/components/csspin-python/-/merge_requests/122>`_)
- Reduce setuptools verbosity in default mode when running
  ``python:wheel`` (`!120
  <https://code.contact.de/pod/components/csspin-python/-/merge_requests/120>`_)
- Add SonarQube analysis (`!119
  <https://code.contact.de/pod/components/csspin-python/-/merge_requests/119>`_)
- Remove the pytest ``--cov-report=html`` export since it was never
  used (`#84
  <https://code.contact.de/pod/components/csspin-python/-/work_items/84>`_)

v4.1.0
======

June 30, 2026

Enhancements
------------

- Add ``python_sbom`` plugin for creating Python SBOMs (`!110
  <https://code.contact.de/pod/components/csspin-python/-/merge_requests/110>`_)

Chores
------

- Add platform identifier to SBOM file name (`!112
  <https://code.contact.de/pod/components/csspin-python/-/merge_requests/112>`_)
- Enrich SBOM during python-sbom task (`!113
  <https://code.contact.de/pod/components/csspin-python/-/merge_requests/113>`_)
- Don't terminate when ``aws_auth.client_secret`` isn't set (`#123
  <https://code.contact.de/pod/components/csspin-python/-/work_items/123>`_)

v4.0.0
======

March 26, 2026

Breaking Changes
----------------

- Drop Python 3.9 Support (`#114
  <https://code.contact.de/pod/components/csspin-python/-/issues/114>`_)

Bug Fixes
---------

- Provision fails when python.venv exists and is empty (`#118
  <https://code.contact.de/pod/components/csspin-python/-/issues/118>`_)
- aws_auth + uv_provisioner: Malformed uv.toml after key_duration expired (`#121
  <https://code.contact.de/pod/components/csspin-python/-/issues/121>`_)

v3.2.0
======

January 14, 2026

Enhancements
------------

- Provide a convenient way to update all Python packages in the provisioned
  environment (`#73 <https://code.contact.de/pod/components/csspin-python/-/issues/73>`_)

Bug Fixes
---------

- ``spin provision`` does not update devpackages properly
  (`#72 <https://code.contact.de/pod/components/csspin-python/-/issues/72>`_)
- Provision with new packages for existing environments results in installation
  of wrong versions (`#109
  <https://code.contact.de/pod/components/csspin-python/-/issues/109>`_)

Chores
------

- Add repository URL information to Wheel metadata
  (`#112 <https://code.contact.de/pod/components/csspin-python/-/issues/112>`_)
- Update release process documentation and contribution guideline
  (`#113 <https://code.contact.de/pod/components/csspin-python/-/issues/113>`_)

v3.1.1
======

December 12, 2025

Bug Fixes
---------

- python: uv_provisioner fails during uv.toml update
  (`#108 <https://code.contact.de/pod/components/csspin-python/-/issues/108>`_)

Chores
------

- Configure AWS secret handling via configuration tree instead of relying on
  environment variables
  (`#98 <https://code.contact.de/pod/components/csspin-python/-/issues/98>`_)
- Document host system requirements properly
  (`#104 <https://code.contact.de/pod/components/csspin-python/-/issues/104>`_)
- Add release notes to the documentation structure
  (`#100 <https://code.contact.de/pod/components/csspin-python/-/issues/100>`_)
