# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2026 CONTACT Software GmbH
# https://www.contact-software.com/
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Predict the wheel filename ``setup.py bdist_wheel`` would produce, without
building it::

    python _predict_wheel_filename.py /path/to/project NAME VERSION

Must run in the subprocess environment to have setuptools in the environment and
to have the correct Python version and platform tags that the wheel is built
for.
"""

import io
import os
import sys
import warnings
from contextlib import redirect_stdout


def predict_wheel_filename(project_path: str, name: str, version: str) -> str:
    """Return the predicted wheel filename for ``project_path``."""
    os.chdir(project_path)

    # setup.py is exec'd here and free to print, so keep its chatter off the
    # stdout the caller parses. stderr stays, so tracebacks still surface.
    with warnings.catch_warnings(), redirect_stdout(io.StringIO()):
        warnings.simplefilter("ignore")
        if os.path.exists("setup.py"):
            from distutils.core import run_setup  # pylint: disable=deprecated-module

            dist = run_setup(
                "setup.py", script_args=["bdist_wheel"], stop_after="commandline"
            )
        else:
            from setuptools.dist import Distribution

            dist = Distribution({"script_args": ["bdist_wheel"]})
            dist.parse_config_files()

        dist.metadata.name = name
        dist.metadata.version = version

        cmd = dist.get_command_obj("bdist_wheel")
        cmd.ensure_finalized()
        python_tag, abi_tag, plat_tag = cmd.get_tag()  # type: ignore[attr-defined]
        dist_name = cmd.wheel_dist_name  # type: ignore[attr-defined]

    return f"{dist_name}-{python_tag}-{abi_tag}-{plat_tag}.whl"


if __name__ == "__main__":
    print(predict_wheel_filename(*sys.argv[1:4]))
