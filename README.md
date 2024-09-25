# spin_python

This repository contains the spin plugin-package spin_python. It provides the
following spin-plugins:

The following are copied from:
https://code.contact.de/qs/spin/cs.spin/-/commit/a6cd9906504e9761a5b888add26dfe0d62809bd7

-   spin_python.python
-   spin_python.devpi
-   spin_python.radon

The following plugins were copied from:
https://code.contact.de/qs/tooling/spin-plugins/-/commit/87399f327a5979c3ef5619291cd12bc26fce04ac

-   spin_python.pytest
-   spin_python.behave

Additional plugins:

-   python.playwright

## Creating a New Release

The version scheme used is `major.minor.patch` while following the well-known
standards @CONTACT (https://wiki.contact.de/index.php/Versionsnummer).

**Steps to create a release:**

0. Preparations:
    - Verify that all relevant changes are merged into the branch of which the
      release is based.
    - Also make sure that the latest non-scheduled pipeline for that branch is
      green.
1. Enter the Repository within GitLab > Releases > New Release, select the
   desired branch and tag. Further down, enter the release notes including a
   list of changes (e.g. link issue + related MR) and further information that
   might be useful.
2. Hit "Create release" ✨
