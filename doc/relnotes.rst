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

    - Add release notes to the documentation structure (`#100 <https://code.contact.de/qs/spin/cs.spin/-/issues/100>`_)


=============
Release Notes
=============

v4.0.0
======

March 26, 2026

Breaking Changes
----------------

- Drop Python 3.9 Support (`#114
  <https://code.contact.de/qs/spin/spin_python/-/issues/114>`_)

Bug Fixes
---------

- Provision fails when python.venv exists and is empty (`#118
  <https://code.contact.de/qs/spin/spin_python/-/issues/118>`_)
- aws_auth + uv_provisioner: Malformed uv.toml after key_duration expired (`#121
  <https://code.contact.de/qs/spin/spin_python/-/issues/121>`_)

v3.2.0
======

January 14, 2026

Enhancements
------------

- Provide a convenient way to update all Python packages in the provisioned
  environment (`#73 <https://code.contact.de/qs/spin/spin_python/-/issues/73>`_)

Bug Fixes
---------

- ``spin provision`` does not update devpackages properly
  (`#72 <https://code.contact.de/qs/spin/spin_python/-/issues/72>`_)
- Provision with new packages for existing environments results in installation
  of wrong versions (`#109
  <https://code.contact.de/qs/spin/spin_python/-/issues/109>`_)

Chores
------

- Add repository URL information to Wheel metadata
  (`#112 <https://code.contact.de/qs/spin/spin_python/-/issues/112>`_)
- Update release process documentation and contribution guideline
  (`#113 <https://code.contact.de/qs/spin/spin_python/-/issues/113>`_)

v3.1.1
======

December 12, 2025

Bug Fixes
---------

- python: uv_provisioner fails during uv.toml update
  (`#108 <https://code.contact.de/qs/spin/spin_python/-/issues/108>`_)

Chores
------

- Configure AWS secret handling via configuration tree instead of relying on
  environment variables
  (`#98 <https://code.contact.de/qs/spin/spin_python/-/issues/98>`_)
- Document host system requirements properly
  (`#104 <https://code.contact.de/qs/spin/spin_python/-/issues/104>`_)
- Add release notes to the documentation structure
  (`#100 <https://code.contact.de/qs/spin/spin_python/-/issues/100>`_)
