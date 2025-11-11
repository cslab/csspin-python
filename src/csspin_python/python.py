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
#
# pylint: disable=too-few-public-methods,missing-class-docstring,too-many-lines

"""``python``
==========

This plugin provisions the requested version of the Python
programming languages.

On Linux and macOS, Python is installed by compiling from source
(implying, that Python's build requirements must be installed). On
Windows, pre-built binaries are downloaded using `nuget`.

If a user has `pyenv <https://github.com/pyenv/pyenv>`_ installed it
can be activated by setting ``python.user_pyenv`` in
:file:`global.yaml`.

To skip provisioning of Python and use an already installed version,
:py:data:`python.use` can be set to the name or the full path of an
interpreter:

.. code-block:: console

   spin -p python.use=/usr/local/bin/python ...

Note: `spin` will install or update certain packages of that
interpreter, thus write access is required.

Tasks
-----

.. click:: csspin_python:python
   :prog: spin python

.. click:: csspin_python:python:wheel
   :prog: spin python:wheel

.. click:: csspin_python:env
   :prog: spin env

Properties
----------

* :py:data:`python.version` -- must be set to choose the
  required Python version
* :py:data:`python.interpreter` -- path to the Python interpreter

Note: don't use these properties when using `virtualenv`, they will
point to the base installation.

"""

import abc
import configparser
import hashlib
import logging
import os
import re
import shutil
import sys
from subprocess import check_output
from textwrap import dedent, indent
from typing import Iterable, Type, Union

try:
    from typing import Self  # type: ignore[attr-defined]
except ImportError:
    from typing import TypeVar

    Self = TypeVar("Self")  # type: ignore[misc]

from click.exceptions import Abort
from csspin import (
    EXPORTS,
    Command,
    Memoizer,
    Path,
    Verbosity,
    argument,
    backtick,
    cd,
    config,
    die,
    download,
    echo,
    error,
    exists,
    get_requires,
    info,
    interpolate1,
    memoizer,
    mkdir,
    namespaces,
    normpath,
    readtext,
    rmtree,
    setenv,
    sh,
    task,
    warn,
    writetext,
)
from csspin.tree import ConfigTree

defaults = config(
    build_wheels=["{spin.project_root}"],
    pyenv=config(
        url="https://github.com/pyenv/pyenv.git",
        path="{spin.data}/pyenv",
        cache="{spin.data}/pyenv_cache",
        python_build="{python.pyenv.path}/plugins/python-build/bin/python-build",
    ),
    user_pyenv=False,
    nuget=config(
        url="https://dist.nuget.org/win-x86-commandline/latest/nuget.exe",
        exe="{spin.data}/nuget.exe",
        source="https://api.nuget.org/v3/index.json",
    ),
    version=None,
    use=None,
    inst_dir=(
        "{spin.data}/python/{python.version}"
        if sys.platform != "win32"
        else "{spin.data}/python/python.{python.version}/tools"
    ),
    interpreter=(
        "{python.inst_dir}/bin/python{platform.exe}"
        if sys.platform != "win32"
        else "{python.inst_dir}/python{platform.exe}"
    ),
    venv="{spin.spin_dir}/venv",
    memo="{python.venv}/spininfo.memo",
    bindir="{python.venv}/bin" if sys.platform != "win32" else "{python.venv}",
    scriptdir=(
        "{python.venv}/bin" if sys.platform != "win32" else "{python.venv}/Scripts"
    ),
    python="{python.scriptdir}/python{platform.exe}",
    provisioner=None,
    provisioner_memo="{spin.spin_dir}/python_provisioner.memo",
    aws_auth=config(
        enabled=False,
        memo="{spin.spin_dir}/aws_auth.memo",
        key_duration=3600 * 10,  # 10 hours
        static_oidc=False,
        index="16.0/simple",
    ),
    index_url="https://pypi.org/simple",
    requires=config(
        python=["build", "wheel"],
        system=config(
            debian=config(
                apt=[
                    "build-essential",
                    "curl",
                    "git",
                    "libbz2-dev",
                    "libffi-dev",
                    "libkrb5-dev",
                    "liblzma-dev",
                    "libncursesw5-dev",
                    "libreadline-dev",
                    "libsqlite3-dev",
                    "libssl-dev",
                    "libxml2-dev",
                    "libxmlsec1-dev",
                    "make",
                    "xz-utils",
                    "zlib1g-dev",
                ]
            )
        ),
    ),
)


@task()
def python(args: Iterable[object]) -> None:
    """Run the Python interpreter used for this projects."""
    sh("python", *args)


@task("python:wheel", when="package")
def wheel(
    cfg: ConfigTree,
    paths: argument(type=str, nargs=-1, required=False),  # type: ignore[valid-type]
) -> None:
    """Build a wheel of the current project and any additional wheels."""
    setenv(PIP_INDEX_URL=cfg.python.index_url)
    search_paths = paths or cfg.python.build_wheels
    for build_path in {Path(path).absolute() for path in search_paths}:
        try:
            echo("Building PEP 517-like wheel")
            sh(
                "python",
                "-m",
                "build",
                "-w",
                build_path,
                "-o",
                "{spin.project_root}/dist",
            )
        except Abort:
            echo("Building does not seem to work, use legacy setup.py style")
            with cd(build_path):
                sh(
                    "python",
                    "setup.py",
                    None if cfg.verbosity > Verbosity.NORMAL else "-v" "build",
                    "-b",
                    "{spin.project_root}/build",
                    "bdist_wheel",
                    "-d",
                    "{spin.project_root}/dist",
                )


@task()
def env() -> None:
    """
    Generate command to activate the virtual environment

    NOTE: spin itself should not be run from within the activated virtual
          environment!
    """
    if sys.platform == "win32":
        # Don't care about cmd
        print(normpath("{python.scriptdir}", "activate.ps1"))
    else:
        print(f". {normpath('{python.scriptdir}', 'activate')}")


def pyenv_install(cfg: ConfigTree) -> None:
    """Install and setup the virtual environment using pyenv"""
    with namespaces(cfg.python):
        if cfg.python.user_pyenv:
            info("Using your existing pyenv installation ...")
            sh("pyenv", "install", "--skip-existing", {cfg.python.version})
            cfg.python.interpreter = backtick("pyenv which python --nosystem").strip()
        else:
            info("Installing Python {version} to {inst_dir}")
            # For Linux/macOS using the 'python-build' plugin from
            # pyenv is by far the most robust way to install a
            # version of Python.
            if not exists("{pyenv.path}"):
                sh("git", "clone", cfg.python.pyenv.url, cfg.python.pyenv.path)
            else:
                with cd(cfg.python.pyenv.path):
                    sh("git", "pull")
            # we should set
            setenv(PYTHON_BUILD_CACHE_PATH=mkdir(cfg.python.pyenv.cache))
            setenv(PYTHON_CFLAGS="-DOPENSSL_NO_COMP")
            try:
                sh(
                    cfg.python.pyenv.python_build,
                    cfg.python.version,
                    cfg.python.inst_dir,
                )
            except Abort:
                error("Failed to build the Python interpreter - removing it")
                rmtree(cfg.python.inst_dir)
                raise


def nuget_install(cfg: ConfigTree) -> None:
    """Install the virtual environment using nuget"""
    if not exists(cfg.python.nuget.exe):
        download(cfg.python.nuget.url, cfg.python.nuget.exe)
    setenv(NUGET_HTTP_CACHE_PATH=cfg.spin.data / "nugetcache")
    sh(
        cfg.python.nuget.exe,
        "install",
        "-verbosity",
        "quiet",
        "-o",
        cfg.spin.data / "python",
        "python",
        "-version",
        cfg.python.version,
        "-source",
        cfg.python.nuget.source,
    )
    sh(cfg.python.interpreter, "-m", "ensurepip", "--upgrade")
    sh(
        cfg.python.interpreter,
        "-mpip",
        None if cfg.verbosity > Verbosity.NORMAL else "-q",
        "install",
        "-U",
        "pip",
        "wheel",
        "packaging",
    )


def provision(cfg: ConfigTree) -> None:
    """Provision the python plugin"""
    with memoizer(cfg.python.provisioner_memo) as memo:
        if cfg.python.provisioner is None:
            cfg.python.provisioner = SimpleProvisioner(cfg)
        if not memo.check(cfg.python.provisioner):
            memo.add(cfg.python.provisioner)

    if not shutil.which(cfg.python.interpreter):
        cfg.python.provisioner.provision_python(cfg)

    venv_provision(cfg)

    cfg.python.site_packages = get_site_packages(interpreter=cfg.python.python)


def configure(cfg: ConfigTree) -> None:
    """Configure the python plugin"""
    if not cfg.python.version and not cfg.python.use:
        die(
            "Please choose a version in spinfile.yaml by setting python.version"
            " or pass a local interpreter via python.use."
        )

    if cfg.python.use:
        if cfg.python.version:
            warn("python.version will be ignored, using '{python.use}' instead.")
        cfg.python.interpreter = cfg.python.use

    elif cfg.python.user_pyenv:
        setenv(PYENV_VERSION="{python.version}")
        try:
            cfg.python.interpreter = backtick(
                "pyenv which python --nosystem",
                check=False,
                silent=not cfg.verbosity > Verbosity.NORMAL,
            ).strip()
        except Exception:  # pylint: disable=broad-exception-caught # nosec
            warn(
                "The desired interpreter is not available within the"
                " user's pyenv installation."
            )

    if exists(cfg.python.python):
        cfg.python.site_packages = get_site_packages(interpreter=cfg.python.python)

    if cfg.python.aws_auth.enabled:
        _check_aws_token_validity(cfg)


def init(cfg: ConfigTree) -> None:
    """Initialize the python plugin"""
    if not cfg.python.use:
        logging.debug("Checking for %s", cfg.python.interpreter)
        if not exists(cfg.python.interpreter):
            die(
                f"Python {cfg.python.version} has not been provisioned for this"
                " project. You might want to run spin with the 'provision'"
                " task."
            )
    venv_init(cfg)


# We won't activate more than once.
ACTIVATED = False


def venv_init(cfg: ConfigTree) -> None:
    """Activate the virtual environment"""
    global ACTIVATED  # pylint: disable=global-statement
    if os.environ.get("VIRTUAL_ENV", "") != cfg.python.venv and not ACTIVATED:
        activate_this = cfg.python.scriptdir / "activate_this.py"
        if not exists(activate_this):
            die(
                f"{cfg.python.venv} does not exist. You may want to provision"
                " it using 'spin provision'"
            )
        if sys.platform == "win32":
            echo(f"{cfg.python.scriptdir}\\activate.ps1")
        else:
            echo(f". {cfg.python.scriptdir}/activate")
        with open(activate_this, encoding="utf-8") as file:
            exec(  # pylint: disable=exec-used # nosec
                file.read(), {"__file__": activate_this}
            )
        ACTIVATED = True


class ActivateScriptPatcher(abc.ABC):
    activatescript: Union[str, Path]
    setpattern: str
    resetpattern: str
    old_env_pattern: str
    patchmarker: str
    replacements: list[tuple[str, str]]
    script: str

    @staticmethod
    @abc.abstractmethod
    def interpolate_environ_value(value: str) -> str:
        """
        Translate value so the script can handle uninterpolated "{ENVVAR}" literals in value

        Example:
        # Assume the following subset of os.environ
        os.environ = {
            "PATH": "/bin:/usr/bin",
            "COMPILER_PATHS": "/compiler/A/bin:/compiler/B/bin",
        }

        # Now, setenv has been called with
        # setenv(PATH="{python.scriptdir}:{COMPILER_PATHS}:{PATH}") thus the
        # value of ``PATH`` in ``EXPORTS`` equals "/venv/bin:{COMPILER_PATHS}:{PATH}" as
        # ``COMPILER_PATHS`` and ``PATH`` haven't been interpolated yet.
        interpolate_environ_value(value) => /venv/bin:/compiler/A/bin:/compiler/B/bin:/bin:/usr/bin
        """
        return value


def patch_activate(schema: Type[ActivateScriptPatcher]) -> None:
    """Patch the activate script"""
    if exists(schema.activatescript):
        setters = []
        resetters = set()
        old_value_setters = set()
        for name, value in EXPORTS:
            value = schema.interpolate_environ_value(value)
            setters.append(schema.setpattern.format(name=name, value=value))
            resetters.add(schema.resetpattern.format(name=name))
            old_value_setters.add(schema.old_env_pattern.format(name=name))
        resetters_string = "\n".join(resetters)
        setters_string = "\n".join(setters)
        old_value_setters_string = "\n".join(old_value_setters)
        original = readtext(schema.activatescript)
        if schema.patchmarker not in original:
            shutil.copyfile(
                interpolate1(f"{schema.activatescript}"),
                interpolate1(f"{schema.activatescript}.bak"),
            )
        info(f"Patching {schema.activatescript}")
        # Removing the byte order marker (BOM) ensures the absence of those in
        # the final scripts. BOMs in executables are not fully supported in
        # Powershell.
        original = (
            readtext(f"{schema.activatescript}.bak").encode("utf-8").decode("utf-8-sig")
        )
        for repl in schema.replacements:
            original = original.replace(repl[0], repl[1])
        newscript = schema.script.format(
            patchmarker=schema.patchmarker,
            original=original,
            resetters=resetters_string,
            old_value_setters=old_value_setters_string,
            setters=setters_string,
        )
        writetext(f"{schema.activatescript}", newscript)


class BashActivate(ActivateScriptPatcher):
    patchmarker = "\n## Patched by csspin_python.python\n"
    activatescript = Path("{python.scriptdir}") / "activate"
    replacements = [
        ("deactivate", "origdeactivate"),
    ]
    old_env_pattern = dedent(
        """
        if [ -z ${{{name}+x}} ]; then
            export _OLD_SPIN_UNSET{name}=""
        else
            export _OLD_SPIN_VALUE{name}="${name}"
        fi
        """
    )
    setpattern = dedent(
        """
        {name}="{value}"
        export {name}
        """
    )
    resetpattern = indent(
        dedent(
            """
            if ! [ -z "${{_OLD_SPIN_VALUE{name}+_}}" ] ; then
                {name}="$_OLD_SPIN_VALUE{name}"
                export {name}
                unset _OLD_SPIN_VALUE{name}
            fi
            if ! [ -z "${{_OLD_SPIN_UNSET{name}+_}}" ] ; then
                unset {name}
                unset _OLD_SPIN_UNSET{name}
            fi
            """
        ),
        prefix="    ",
    )
    script = dedent(
        """
        {patchmarker}
        {original}
        deactivate () {{
            {resetters}
            if [ ! "${{1-}}" = "nondestructive" ] ; then
                # Self destruct!
                unset -f deactivate
                origdeactivate
            fi
        }}

        deactivate nondestructive
        {old_value_setters}
        {setters}

        # The hash command must be called to get it to forget past
        # commands. Without forgetting past commands the $PATH changes
        # we made may not be respected
        hash -r 2>/dev/null
        """
    )

    @staticmethod
    def interpolate_environ_value(value: str) -> str:
        if not value:
            return ""
        keys = re.findall(r"{(?P<key>\w+?)}", value)
        for key in keys:
            if key in os.environ:
                value = value.replace(f"{{{key}}}", f"${key}")
        return value


class PowershellActivate(ActivateScriptPatcher):
    patchmarker = "\n## Patched by csspin_python.python\n"
    activatescript = Path("{python.scriptdir}") / "activate.ps1"
    replacements = [
        ("deactivate", "origdeactivate"),
    ]
    old_env_pattern = (
        "New-Variable -Scope global -Name _OLD_SPIN_{name} -Value $env:{name}"
    )
    setpattern = dedent(
        """
        $env:{name} = "{value}"
        """
    )
    resetpattern = indent(
        dedent(
            """
                if (Test-Path variable:_OLD_SPIN_{name}) {{
                    $env:{name} = $variable:_OLD_SPIN_{name}
                    Remove-Variable "_OLD_SPIN_{name}" -Scope global
                }}
            """
        ),
        prefix="    ",
    )
    script = dedent(
        """
        {patchmarker}
        {original}
        function global:deactivate([switch] $NonDestructive) {{
            {resetters}
            if (!$NonDestructive) {{
                Remove-Item function:deactivate
                origdeactivate
            }}
        }}

        deactivate -nondestructive
        {old_value_setters}
        {setters}
        """
    )

    @staticmethod
    def interpolate_environ_value(value: str) -> str:
        if not value:
            return ""
        keys = re.findall(r"{(?P<key>\w+?)}", value)
        for key in keys:
            if key in os.environ:
                value = value.replace(f"{{{key}}}", f"$env:{key}")
        return value


class BatchActivate(ActivateScriptPatcher):
    patchmarker = "\nREM Patched by csspin_python.python\n"
    activatescript = Path("{python.scriptdir}") / "activate.bat"
    replacements = []
    old_env_pattern = dedent(
        """
        if defined _OLD_SPIN_VALUE_{name} goto ENDIFSPIN{name}1
        if defined _OLD_SPIN_UNSET_{name} goto ENDIFSPIN{name}2
        if defined {name} goto ENDIFSPIN{name}3
        goto ENDIFSPIN{name}4
        :ENDIFSPIN{name}1
            set "{name}=%_OLD_SPIN_VALUE_{name}%"
            set "_OLD_SPIN_VALUE_{name}=%{name}%"
            goto ENDIFSPIN{name}5
        :ENDIFSPIN{name}2
            set "{name}="
            set "_OLD_SPIN_UNSET_{name}= "
            goto ENDIFSPIN{name}5
        :ENDIFSPIN{name}3
            set "_OLD_SPIN_VALUE_{name}=%{name}%"
            goto ENDIFSPIN{name}5
        :ENDIFSPIN{name}4
            set "_OLD_SPIN_UNSET_{name}= "
            goto ENDIFSPIN{name}5
        :ENDIFSPIN{name}5
        """
    )
    setpattern = 'set "{name}={value}"'
    resetpattern = ""
    script = dedent(
        """
        @echo off
        {patchmarker}
        {original}
        {old_value_setters}
        {setters}
        """
    )

    @staticmethod
    def interpolate_environ_value(value: str) -> str:
        if not value:
            return ""
        keys = re.findall(r"{(?P<key>\w+?)}", value)
        for key in keys:
            if key in os.environ:
                value = value.replace(f"{{{key}}}", f"%{key}%")
        return value


class BatchDeactivate(ActivateScriptPatcher):
    patchmarker = "\nREM Patched by csspin_python.python\n"
    activatescript = Path("{python.scriptdir}") / "deactivate.bat"
    replacements = []
    old_env_pattern = ""
    setpattern = ""
    resetpattern = dedent(
        """
        if defined _OLD_SPIN_VALUE_{name} goto ENDIFVSPIN{name}1
        if defined _OLD_SPIN_UNSET_{name} goto ENDIFVSPIN{name}2
        :ENDIFVSPIN{name}1
            set "{name}=%_OLD_SPIN_VALUE_{name}%"
            set _OLD_SPIN_VALUE_{name}=
            goto ENDIFVSPIN{name}0
        :ENDIFVSPIN{name}2
            set {name}=
            set _OLD_SPIN_UNSET_{name}=
            goto ENDIFVSPIN{name}0
        :ENDIFVSPIN{name}0
        """
    )
    script = dedent(
        """
        @echo off
        {patchmarker}
        {original}
        {resetters}
        """
    )


class PythonActivate(ActivateScriptPatcher):
    patchmarker = "# Patched by csspin_python.python\n"
    activatescript = Path("{python.scriptdir}") / "activate_this.py"
    replacements = []
    old_env_pattern = ""
    setpattern = 'os.environ["{name}"] = fr"{value}"'
    resetpattern = ""
    script = dedent(
        """
        {patchmarker}
        {original}
        {setters}
        """
    )

    @staticmethod
    def interpolate_environ_value(value: str) -> str:
        if not value:
            return ""
        keys = re.findall(r"{(?P<key>\w+?)}", value)
        for key in keys:
            if key in os.environ:
                value = value.replace(f"{{{key}}}", f"{{os.environ['{key}']}}")
        return value


def get_site_packages(interpreter: Path) -> Path:
    """Return the path to the virtual environments site-packages."""
    return Path(
        check_output(
            [
                interpolate1(interpreter),
                "-c",
                'import sysconfig; print(sysconfig.get_path("purelib"))',
            ],
        )
        .decode()
        .strip(),
    )


def finalize_provision(cfg: ConfigTree) -> None:
    """Patching the activate scripts and preparing the site-packages"""
    cfg.python.provisioner.install(cfg)

    for schema in (
        BashActivate,
        BatchActivate,
        BatchDeactivate,
        PowershellActivate,
        PythonActivate,
    ):
        patch_activate(schema)

    setenv_path = str(cfg.python.site_packages / "_set_env.pth")
    info(f"Create {setenv_path}")
    pthline = interpolate1(
        "import os; "
        "bindir=r'{python.bindir}'; "
        "os.environ['PATH'] = "
        "os.environ['PATH'] if bindir in os.environ['PATH'] "
        "else os.pathsep.join((bindir, os.environ['PATH']))\n"
    )
    writetext(setenv_path, pthline)


class ProvisionerProtocol:
    """An implementation of this protocol is used to provision
    requirements to a virtual environment.

    Separate plugins, can implement this interface and overwrite
    cfg.python.provisioner.

    .. note::
    The provisioner will be memoized, so make sure it works with ``pickle.dumps``.
    """

    _requirements: set[str] = set()

    def provision_python(self: Self, cfg: ConfigTree) -> None:
        """Provision the project's python interpreter"""
        if sys.platform == "win32":
            nuget_install(cfg)
        else:
            # Everything else (Linux and macOS) uses pyenv
            pyenv_install(cfg)

    # noinspection PyMethodMayBeStatic
    def provision_venv(self: Self, cfg: ConfigTree) -> None:
        """Provision the virtual environment of the project"""
        cmd = [
            sys.executable,
            "-mvirtualenv",
            None if cfg.verbosity > Verbosity.NORMAL else "-q",
        ]
        virtualenv = Command(*cmd)
        # do not download seeds, since we update pip later anyway
        # add the plugins directory to the PYTHONPATH so that virtualenv will be found
        virtualenv(
            "-p",
            cfg.python.interpreter,
            cfg.python.venv,
            env={"PYTHONPATH": cfg.spin.spin_dir / "plugins"},
        )

    def prerequisites(self: Self, cfg: ConfigTree) -> None:
        """Provide requirements for the provisioning strategy."""

    def add(
        self: Self, cfg: ConfigTree, req: str  # pylint: disable=unused-argument
    ) -> None:
        """
        Add a single requirement `req`, that will be installed into the
        environment.
        """
        self._requirements.add(req)

    def install(self: Self, cfg: ConfigTree) -> None:
        """Install the requirements"""

    def cleanup(self: Self, cfg: ConfigTree) -> None:
        """Cleanup the provisioned environment"""
        rmtree(cfg.python.venv)


class SimpleProvisioner(ProvisionerProtocol):
    """
    The simplest Python provisioner, using pip.

    This provisioner will never uninstall requirements that are no longer
    required.
    """

    def __init__(self: Self, cfg: ConfigTree) -> None:
        self._m = Memoizer(interpolate1("{python.memo}"))
        self._install_command = Command(
            "pip",
            None if cfg.verbosity > Verbosity.NORMAL else "-q",
            "--disable-pip-version-check",
            "install",
            *[f"--constraint={constraint}" for constraint in cfg.python.constraints],
        )

    def prerequisites(self: Self, cfg: ConfigTree) -> None:
        # We'll need pip
        sh(
            "python",
            "-mpip",
            None if cfg.verbosity > Verbosity.NORMAL else "-q",
            "--disable-pip-version-check",
            "install",
            "--index-url",
            cfg.python.index_url,
            "-U",
            "pip",
        )

    def install(self: Self, cfg: ConfigTree) -> None:
        if requirements := self._filter(
            self._requirements, self._m, cfg.spin.project_root
        ):
            self._install_command(*self._split(requirements))
            self._m.clear()
            for req in requirements:
                self._m.add(_req_for_memo(req, cfg.spin.project_root))

    @staticmethod
    def _split(requirements: Iterable[str]) -> list[str]:
        """Used to pass whitespace-less args to :func:`csspin.sh()`."""
        requirement_list = []
        for requirement in requirements:
            requirement_list.extend(requirement.split())
        return requirement_list

    @staticmethod
    def _filter(
        requirements: set[str], memo: Memoizer, project_root: Union[Path, str]
    ) -> set[str]:
        """
        We want to filter all requirements prior to installing them, because we
        only want to run the install, when there are changes, as it takes pip
        quite some time to check, whether it has to do something.
        """
        if all(memo.check(_req_for_memo(req, project_root)) for req in requirements):
            return set()
        else:
            return requirements


def _file_hash(filename: Union[Path, str]) -> str:
    """
    Calculate a sha256 hash of a file's content and return its hexdigest.
    """
    with open(filename, mode="br") as fd:
        return hashlib.sha256(fd.read()).hexdigest()  # nosec: hashlib


def _split_requirement_option(req: str, project_root: Path) -> Union[Path, None]:
    """
    Takes an element of ``python.requirements`` and checks if it
    is an argument for pip that contains a filename. If so,
    the filename will be returned, ``None`` otherwise.

    The following options are respected:
        - ``-r``/``--requirement``
        - ``-c``/``--constraint``

    If a file for an option cannot be found, the plugin will
    :func:`csspin.die()`.
    """
    if (
        req.startswith(option := "-r")
        or req.startswith(option := "--requirement")
        or req.startswith(option := "-c")
        or req.startswith(option := "--constraint")
    ):
        # The pattern has to enforce the " "/"=" for the long-options
        match_many = "+" if option.startswith("--") else "*"
        pattern = rf"{option}[ =]{match_many}(?P<filename>.*)"
        match = re.match(pattern, req)
        if not match:
            die(f"{req} could not be validated.")
        else:
            file = project_root / match.group("filename")
            if not file.exists():
                die(f"{file} does not exist.")
            return file
    return None


def _req_for_memo(
    req: str, project_root: Union[Path, str]
) -> str:  # pylint: disable=inconsistent-return-statements
    """
    Return a memoizable representation of a python requirement. In case a
    requirement is on of the following options, the function returns requirement
    with a hash of the files' content appended. Otherwise the requirement itself
    will be returned.
    """
    if file := _split_requirement_option(req, project_root):
        return f"{req}{_file_hash(file)}"
    else:
        return req


def venv_provision(  # pylint: disable=too-many-branches,missing-function-docstring
    cfg: ConfigTree,
) -> None:
    fresh_env = False

    info("Checking venv '{python.venv}'")
    if not exists(cfg.python.venv):
        info("Provisioning venv '{python.venv}'")
        cfg.python.provisioner.provision_venv(cfg)
        fresh_env = True

    # This sets PATH to the venv
    init(cfg)

    _configure_pipconf(cfg)

    # Establish the prerequisites
    if fresh_env:
        cfg.python.provisioner.prerequisites(cfg)

    # Plugins can define a 'venv_hook' function, to give them a
    # chance to do something with the virtual environment just
    # being provisioned (e.g. preparing the venv by adding .pth
    # files or by adding packages with other installers like
    # easy_install).
    for plugin in cfg.spin.topo_plugins:
        plugin_module = cfg.loaded[plugin]
        hook = getattr(plugin_module, "venv_hook", None)
        if hook is not None:
            logging.debug(f"{plugin_module.__name__}.venv_hook()")
            hook(cfg)

    # Add packages required by the project ('requirements')
    for req in cfg.python.get("requirements", []):
        cfg.python.provisioner.add(cfg, interpolate1(req))

    # Install packages required by plugins used
    # ('<plugin>.requires.python')
    for plugin in cfg.spin.topo_plugins:
        plugin_module = cfg.loaded[plugin]
        for req in get_requires(plugin_module.defaults, "python"):
            cfg.python.provisioner.add(cfg, interpolate1(req))


def cleanup(cfg: ConfigTree) -> None:
    """Remove directories and files generated by the python plugin."""
    with memoizer(cfg.python.provisioner_memo) as memo:
        for provisioner in memo.items():
            try:
                provisioner.cleanup(cfg)
            except Exception as err:  # pylint: disable=broad-exception-caught
                warn(
                    "Cleaning up the python environment of provisioner class "
                    f"'{provisioner.__class__.__name__}' failed: {err}"
                )
        memo.clear()

    rmtree(cfg.python.provisioner_memo)
    rmtree(cfg.python.aws_auth.memo)
    for path in cfg.python.build_wheels:
        current_path = Path(interpolate1(path))
        rmtree(current_path / "build")
        rmtree(current_path / "dist")
        for filename in os.listdir(current_path):
            if filename.endswith(".egg-info") or filename.endswith(".dist-info"):
                rmtree(current_path / filename)


def _get_pipconf(cfg: ConfigTree) -> Path:
    """Retrieve the pipconf configuration file path."""
    if sys.platform == "win32":
        pipconf = interpolate1(Path(cfg.python.venv)) / "pip.ini"
    else:
        pipconf = interpolate1(Path(cfg.python.venv)) / "pip.conf"

    return pipconf


def _configure_pipconf(cfg: ConfigTree, update: bool = False) -> None:
    """Configure the pip configuration file"""
    config_parser = configparser.ConfigParser()
    config_parser.read_string(cfg.python.pipconf)
    if not config_parser.has_section("global"):
        config_parser.add_section("global")
    if update or not (
        "index_url" in config_parser["global"] or "index-url" in config_parser["global"]
    ):
        config_parser["global"]["index_url"] = interpolate1(cfg.python.index_url)
    with open(_get_pipconf(cfg), mode="w", encoding="utf-8") as fd:
        config_parser.write(fd)


def _obfuscate_index_url(index_url: str) -> None:
    """Add the CodeArtifact token to the secrets."""

    from csspin import secrets

    secrets.add(index_url.split(":")[2].split("@")[0])  # Codeartifact token


def _check_aws_token_validity(cfg: ConfigTree) -> None:
    """
    If csspin-python[aws_auth] is installed, we can use csaccess to get the
    CodeArtifact authentication token.
    """

    try:
        from csaccess import get_ca_pypi_url_programmatic
    except ImportError:
        die(
            "The 'aws_auth' feature requires the 'aws_auth' extra being"
            " installed (e.g. via csspin-python[aws_auth] in spinfile.yaml)."
        )

    import time

    current_time = int(time.time())
    timestamp_key = "aws_auth_timestamp"

    with memoizer(cfg.python.aws_auth.memo) as memo:
        for item in memo.items():
            if isinstance(item, str) and item.startswith(f"{timestamp_key}:"):
                last_time = int(item.split(":", 1)[1])
                if current_time - last_time < int(
                    interpolate1(cfg.python.aws_auth.key_duration)
                ):
                    pipconf = _get_pipconf(cfg)
                    config_parser = configparser.ConfigParser()
                    config_parser.read(pipconf)
                    info(f"Using existing index URL from {pipconf}.")

                    if index_url := (
                        config_parser["global"].get("index_url")
                        or config_parser["global"].get("index-url")
                    ):
                        cfg.python.index_url = index_url
                        _obfuscate_index_url(index_url)
                    break
                memo.items().remove(item)
        else:
            info("Updating Codeartifact token.")
            from urllib.parse import urljoin

            opts = {
                "static_oidc": interpolate1(cfg.python.aws_auth.static_oidc).lower()
                == "true"
            }
            if cfg.python.aws_auth.client_id:
                opts["client_id"] = interpolate1(cfg.python.aws_auth.client_id)
            if cfg.python.aws_auth.role_arn:
                opts["aws_role_arn"] = interpolate1(cfg.python.aws_auth.role_arn)

            index_base_url = get_ca_pypi_url_programmatic(**opts)
            index_url = urljoin(
                index_base_url + "/", interpolate1(cfg.python.aws_auth.index)
            )
            cfg.python.index_url = index_url
            _obfuscate_index_url(index_url)

            if exists(cfg.python.venv):
                _configure_pipconf(cfg, update=True)
            memo.add(f"{timestamp_key}:{current_time}")
