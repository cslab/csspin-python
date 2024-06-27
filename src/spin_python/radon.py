# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2020 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/

"""Module implementing the radon plugin for cs.spin"""

import logging

from spin import config, info, option, sh, task

defaults = config(
    exe="radon",
    opts=["-n", "{radon.mi_treshold}"],
    mi_treshold="B",
    requires=config(
        spin=[
            "spin_python.python",
        ],
        python=["radon"],
    ),
)


# TODO(wen): is this actually linting? Not sure
@task()
def radon(
    cfg,
    allsource: option("--all", "allsource", is_flag=True),  # noqa: F821
    args,
):
    """Run radon to measure code complexity."""
    if allsource:
        files = ("{spin.project_root}/src", "{spin.project_root}/tests")
    else:
        files = args
        if not files and hasattr(cfg, "vcs") and hasattr(cfg.vcs, "modified"):
            info("Found modified files.")
            files = cfg.vcs.modified
        files = [f for f in files if f.endswith(".py")]
    if files:
        logging.debug(f"radon: Modified files: {files}")
        sh("{radon.exe}", "mi", *cfg.radon.opts, *files)
