# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2022 CONTACT Software GmbH
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

"""Module implementing the pytest plugin for spin"""


from typing import Iterable

from csspin import Path, Verbosity, config, die, option, setenv, sh, task
from csspin.tree import ConfigTree

defaults = config(
    coverage=False,
    coverage_opts=[
        "--cov-reset",
        "--cov",
        "--cov-report=term",
        "--cov-report=html",
        "--cov-report=xml:{pytest.coverage_report}",
    ],
    coverage_report="python-pytest-coverage.xml",
    opts=[],
    tests=["cs", "tests"],  # Strong convention @CONTACT
    test_report="pytest.xml",
    requires=config(
        spin=[
            "csspin_python.debugpy",
            "csspin_python.python",
        ],
        python=[
            "debugpy",
            "pytest",
            "pytest-cov",
        ],
    ),
)


@task(when="test")
def pytest(  # pylint: disable=too-many-arguments,too-many-positional-arguments
    cfg: ConfigTree,
    instance: option(  # type: ignore[valid-type]
        "-i",  # noqa: F821
        "--instance",  # noqa: F821
        default=None,
        help="Directory of the CONTACT Elements instance.",  # noqa: F722
    ),
    coverage: option(  # type: ignore[valid-type]
        "-c",  # noqa: F821
        "--coverage",  # noqa: F821
        is_flag=True,
        help="Run the tests while collecting coverage.",  # noqa: F722
    ),
    debug: option(  # type: ignore[valid-type]
        "--debug", is_flag=True, help="Start debug server."  # noqa: F722,F821
    ),
    with_test_report: option(  # type: ignore[valid-type]
        "--with-test-report",  # noqa: F722
        is_flag=True,
        help="Create a test execution report.",  # noqa: F722
    ),
    args: Iterable[str],
) -> None:
    """Run the 'pytest' command."""
    opts = cfg.pytest.opts
    if cfg.verbosity == Verbosity.QUIET:
        opts.append("-q")
    if with_test_report and cfg.pytest.test_report:
        opts.append(f"--junitxml={cfg.pytest.test_report}")
    if coverage or cfg.pytest.coverage:
        opts.extend(cfg.pytest.coverage_opts)
    if debug:
        cmd = f"debugpy {' '.join(cfg.debugpy.opts)} -m pytest".split()
    else:
        cmd = ["pytest"]

    if cfg.loaded.get("csspin_ce.mkinstance"):
        if not (
            inst := Path(instance or cfg.mkinstance.base.instance_location).absolute()
        ).is_dir():
            die(f"Cannot find CE instance '{inst}'.")

        setenv(CADDOK_BASE=inst)
        sh(*cmd, *opts, *args, *cfg.pytest.tests)
    else:
        sh(*cmd, *opts, *args, *cfg.pytest.tests)
