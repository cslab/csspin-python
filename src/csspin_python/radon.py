# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2020 CONTACT Software GmbH
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

"""Module implementing the radon plugin for spin"""

import logging
from typing import Iterable

from csspin import config, info, option, sh, task
from csspin.tree import ConfigTree

defaults = config(
    exe="radon",
    opts=["-n", "{radon.mi_threshold}"],
    mi_threshold="B",
    requires=config(
        spin=[
            "csspin_python.python",
        ],
        python=["radon"],
    ),
)


@task()
def radon(
    cfg: ConfigTree,
    allsource: option(  # type: ignore[valid-type]
        "--all",  # noqa: F821
        "allsource",  # noqa: F821
        is_flag=True,
        help="Run for all src- and test-files.",  # noqa: F722,F821
    ),
    args: Iterable[str],
) -> None:
    """Run radon to measure code complexity."""
    if allsource:
        files = ["{spin.project_root}/src", "{spin.project_root}/tests"]
    else:
        files = list(args)
        if not files and hasattr(cfg, "vcs") and hasattr(cfg.vcs, "modified"):
            info("Found modified files.")
            files = cfg.vcs.modified
        files = [f for f in files if f.endswith(".py")]
    if files:
        logging.debug(f"radon: Modified files: {files}")
        sh("{radon.exe}", "mi", *cfg.radon.opts, *files)
