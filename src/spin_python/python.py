# -*- mode: python; coding: utf-8 -*-
#
# Copyright (C) 2020 CONTACT Software GmbH
# All rights reserved.
# https://www.contact-software.com/
#
# pylint: disable=too-few-public-methods,missing-class-docstring

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

.. click:: spin_python:python
   :prog: spin python

.. click:: spin_python:python:wheel
   :prog: spin python:wheel

.. click:: spin_python:env
   :prog: spin env

Properties
----------

* :py:data:`python.version` -- must be set to choose the
  required Python version
* :py:data:`python.interpreter` -- path to the Python interpreter

Note: don't use these properties when using `virtualenv`, they will
point to the base installation.

"""

import logging
import os
import shutil
import sys
from textwrap import dedent

from click.exceptions import Abort
from spin import parse_version  # pylint: disable=unused-import # noqa: F401
from spin import (
    EXPORTS,
    Command,
    Memoizer,
    Path,
    Verbosity,
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

defaults = config(
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
    current_package=config(
        install=True,
        extras=[],
    ),
    index_url="https://pypi.org/simple",
)


def system_requirements(
    cfg,
):  # pylint: disable=unused-argument,missing-function-docstring
    # This is our little database of system requirements for
    # provisioning Python; spin identifies platforms by a tuple
    # composed of the distro id and version e.g. ("debian", 10).
    debian_requirements = [
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
    return [
        # We intentionally leave out Tk, as it pulls in a lot of
        # graphics and X packages
        (
            lambda distro, version: distro in ("debian", "mint", "ubuntu"),
            {
                "apt": " ".join(debian_requirements),
            },
        ),
    ]


@task()
def python(args):
    """Run the Python interpreter used for this projects."""
    sh("python", *args)


@task("python:wheel", when="package")
def wheel(cfg):
    """Build a wheel of the current project."""
    setenv(PIP_INDEX_URL=cfg.python.index_url)
    try:
        echo("Building PEP 518 like wheel")
        sh("python", "-m", "build", "-w")
    except Abort:
        echo("Building does not seem to work, use legacy setup.py style")
        sh(
            "python",
            "setup.py",
            None if cfg.verbosity > Verbosity.NORMAL else "-q",
            "build",
            "-b",
            "{spin.spin_dir}/build",
            "bdist_wheel",
            "-d",
            "{spin.spin_dir}/dist",
        )


@task()
def env():
    """Generate command to activate the virtual environment"""
    if sys.platform == "win32":
        # Don't care about cmd
        print(normpath("{python.scriptdir}", "activate.ps1"))
    else:
        print(f". {normpath('{python.scriptdir}', 'activate')}")


def pyenv_install(cfg):
    """Install and setup the virtual environment using pyenv"""
    with namespaces(cfg.python):
        if cfg.python.user_pyenv:
            info("Using your existing pyenv installation ...")
            sh(f"pyenv install --skip-existing {cfg.python.version}")
            cfg.python.interpreter = backtick("pyenv which python --nosystem").strip()
        else:
            info("Installing Python {version} to {inst_dir}")
            # For Linux/macOS using the 'python-build' plugin from
            # pyenv is by far the most robust way to install a
            # version of Python.
            if not exists("{pyenv.path}"):
                sh(f"git clone {cfg.python.pyenv.url} {cfg.python.pyenv.path}")
            else:
                with cd(cfg.python.pyenv.path):
                    sh("git pull")
            # we should set
            setenv(PYTHON_BUILD_CACHE_PATH=mkdir(cfg.python.pyenv.cache))
            setenv(PYTHON_CFLAGS="-DOPENSSL_NO_COMP")
            try:
                sh(
                    f"{cfg.python.pyenv.python_build} {cfg.python.version} {cfg.python.inst_dir}"
                )
            except Abort:
                error("Failed to build the Python interpreter - removing it")
                rmtree(cfg.python.inst_dir)
                raise


def nuget_install(cfg):
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
    sh(f"{cfg.python.interpreter} -m ensurepip --upgrade")
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


def provision(cfg):
    """Provision the python plugin"""
    info(f"Checking {cfg.python.interpreter}")
    if not shutil.which(cfg.python.interpreter):
        if sys.platform == "win32":
            nuget_install(cfg)
        else:
            # Everything else (Linux and macOS) uses pyenv
            pyenv_install(cfg)
    venv_provision(cfg)

    cfg.python.site_packages = get_site_packages(interpreter=cfg.python.python)


def configure(cfg):
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


def init(cfg):
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


def venv_init(cfg):
    """Activate the virtual environment"""
    global ACTIVATED  # pylint: disable=global-statement
    if os.environ.get("VIRTUAL_ENV", "") != cfg.python.venv and not ACTIVATED:
        activate_this = cfg.python.scriptdir / "activate_this.py"
        if not exists(activate_this):
            die(
                f"{cfg.python.venv} does not exist. You may want to provision"
                " it using 'spin provision'"
            )
        echo(f"activate {cfg.python.venv}", resolve=True)
        with open(activate_this, encoding="utf-8") as file:
            exec(  # pylint: disable=exec-used # nosec
                file.read(), {"__file__": activate_this}
            )
        ACTIVATED = True


def patch_activate(cfg, schema):
    """Patch the activate script"""
    if exists(schema.activatescript):
        setters = []
        resetters = []
        for name, value in EXPORTS.items():
            if name == "PATH" and cfg.python.scriptdir not in value:
                # Ensure that the virtual environments scriptdir is in PATH.
                value = cfg.python.scriptdir + os.pathsep + value
            if value:
                setters.append(schema.setpattern.format(name=name, value=value))
                resetters.append(schema.resetpattern.format(name=name, value=value))
        resetters = "\n".join(resetters)
        setters = "\n".join(setters)
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
            resetters=resetters,
            setters=setters,
        )
        writetext(f"{schema.activatescript}", newscript)


class BashActivate:
    patchmarker = "\n## PATCHED BY spin.builtin.virtualenv\n"
    activatescript = Path("{python.scriptdir}") / "activate"
    replacements = [
        ("deactivate", "origdeactivate"),
    ]
    setpattern = dedent(
        """
        _OLD_SPIN_{name}="${name}"
        {name}="{value}"
        export {name}
        """
    )
    resetpattern = dedent(
        """
            if ! [ -z "${{_OLD_SPIN_{name}+_}}" ] ; then
                {name}="$_OLD_SPIN_{name}"
                export {name}
                unset _OLD_SPIN_{name}
            fi
        """
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

        {setters}

        # The hash command must be called to get it to forget past
        # commands. Without forgetting past commands the $PATH changes
        # we made may not be respected
        hash -r 2>/dev/null
        """
    )


class PowershellActivate:
    patchmarker = "\n## PATCHED BY spin.builtin.virtualenv\n"
    activatescript = Path("{python.scriptdir}") / "activate.ps1"
    replacements = [
        ("deactivate", "origdeactivate"),
    ]
    setpattern = dedent(
        """
        New-Variable -Scope global -Name _OLD_SPIN_{name} -Value $env:{name}
        $env:{name} = "{value}"
        """
    )
    resetpattern = dedent(
        """
            if (Test-Path variable:_OLD_SPIN_{name}) {{
                $env:{name} = $variable:_OLD_SPIN_{name}
                Remove-Variable "_OLD_SPIN_{name}" -Scope global
            }}
        """
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

        {setters}
        """
    )


class BatchActivate:
    patchmarker = "\nREM Patched by spin.builtin.virtualenv\n"
    activatescript = Path("{python.scriptdir}") / "activate.bat"
    replacements = ()
    setpattern = dedent(
        """
        if not defined _OLD_SPIN_{name} goto ENDIFSPIN{name}1
            set "{name}=%_OLD_SPIN_{name}%"
        :ENDIFSPIN{name}1
        if defined _OLD_SPIN_{name} goto ENDIFSPIN{name}2
            set "_OLD_SPIN_{name}=%{name}%"
        :ENDIFSPIN{name}2
        set "{name}={value}"
        """
    )
    resetpattern = ""
    script = dedent(
        """
        @echo off
        {patchmarker}
        {original}
        {setters}
        """
    )


class BatchDeactivate:
    patchmarker = "\nREM Patched by spin.builtin.virtualenv\n"
    activatescript = Path("{python.scriptdir}") / "deactivate.bat"
    replacements = ()
    setpattern = ""
    resetpattern = dedent(
        """
        if not defined _OLD_SPIN_{name} goto ENDIFVSPIN{name}
            set "{name}=%_OLD_SPIN_{name}%"
            set _OLD_SPIN_{name}=
        :ENDIFVSPIN{name}
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


class PythonActivate:
    patchmarker = "# Patched by spin.builtin.virtualenv\n"
    activatescript = Path("{python.scriptdir}") / "activate_this.py"
    replacements = ()
    setpattern = 'os.environ["{name}"] = r"{value}"'
    resetpattern = ""
    script = dedent(
        """
        {patchmarker}
        {original}
        {setters}
        """
    )


def get_site_packages(interpreter):
    """Return the path to the virtual environments site-packages."""
    return Path(
        sh(
            interpreter,
            "-c",
            'import sysconfig; print(sysconfig.get_path("purelib"))',
            capture_output=True,
        )
        .stdout.decode()
        .strip()
    )


def finalize_provision(cfg):
    """Patching the activate scripts and preparing the site-packages"""
    cfg.python.provisioner.install(cfg)
    for schema in (
        BashActivate,
        BatchActivate,
        BatchDeactivate,
        PowershellActivate,
        PythonActivate,
    ):
        patch_activate(cfg, schema)

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
    dependencies to a virtual environment.

    Separate plugins, can implement this interface and overwrite
    cfg.python.provisioner.

    """

    def prerequisites(self, cfg):
        """Provide requirements for the provisioning strategy."""

    def lock(self, cfg):
        """Lock the project's dependencies."""

    def add(self, req, devpackage=False):
        """Add an extra dependency (incl. development ones)."""

    def lock_extras(self, cfg):
        """Lock the extra dependencies."""

    def sync(self, cfg):
        """Synchronize the environment with the locked dependencies."""

    def install(self, cfg):
        """Install the project itself."""


class SimpleProvisioner(ProvisionerProtocol):
    """The simplest Python dependency provisioner using pip.

    This provisioner will never uninstall dependencies that are no
    longer required.
    """

    def __init__(self):
        self.requirements = set()
        self.devpackages = set()
        self.m = Memoizer("{python.memo}")

    def prerequisites(self, cfg):
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

    def lock(self, cfg):
        """Noop"""

    def add(self, req, devpackage=False):
        # Add the requirement or devpackage if not already there.
        if not self.m.check(req):
            lst = self.devpackages if devpackage else self.requirements
            lst.add(req)

    def sync(self, cfg):
        self.__execute_installation(
            self.requirements,
            None if cfg.verbosity > Verbosity.NORMAL else "-q",
            cfg.python.index_url,
        )

    def install(self, cfg):
        quietflag = None if cfg.verbosity > Verbosity.NORMAL else "-q"
        self.__execute_installation(self.devpackages, quietflag, cfg.python.index_url)

        # If there is a setup.py, make an editable install (which
        # transitively also installs runtime dependencies of the project).
        if cfg.python.current_package.install and any(
            (exists("setup.py"), exists("setup.cfg"), exists("pyproject.toml"))
        ):
            cmd = [
                "pip",
                quietflag,
                "--disable-pip-version-check",
                "install",
                "--index-url",
                cfg.python.index_url,
                "-e",
            ]
            if cfg.python.current_package.extras:
                cmd.append(f".[{','.join(cfg.python.current_package.extras)}]")
            else:
                cmd.append(".")
            sh(*cmd)

        # Verify dependency compatibility of installed packages
        pip_check = sh(
            "pip",
            "--disable-pip-version-check",
            "check",
            check=False,
            capture_output=True,
        )
        if pip_check.returncode:
            die(pip_check.stdout)

    def _split(self, reqset):
        """to pass whitespace-less args to sh()"""
        reqlist = []
        for req in reqset:
            reqlist.extend(req.split())
        return reqlist

    def __execute_installation(self, packages, quietflag, index_url):
        """Install packages that are not yet memoized"""
        if to_install := {package for package in packages if not self.m.check(package)}:
            sh(
                "pip",
                quietflag,
                "--disable-pip-version-check",
                "install",
                "--index-url",
                index_url,
                *self._split(to_install),
            )
            for package in to_install:
                self.m.add(package)
            self.m.save()


def venv_provision(cfg):  # pylint: disable=too-many-branches,missing-function-docstring
    fresh_virtualenv = False
    if not exists(cfg.python.venv):
        # virtualenv is guaranteed to be available like this
        # as we declared it as one of spin's dependencies
        cmd = [
            sys.executable,
            "-mvirtualenv",
            None if cfg.verbosity > Verbosity.NORMAL else "-q",
        ]
        virtualenv = Command(*cmd)
        # do not download seeds, since we update pip later anyway
        virtualenv("-p", cfg.python.interpreter, cfg.python.venv)
        fresh_virtualenv = True

    # This sets PATH to the venv
    init(cfg)

    if cfg.python.provisioner is None:
        cfg.python.provisioner = SimpleProvisioner()

    if cfg.python.pipconf:
        if sys.platform == "win32":
            pipconf = cfg.python.venv / "pip.ini"
        else:
            pipconf = cfg.python.venv / "pip.conf"
        writetext(pipconf, cfg.python.pipconf)

    # Establish the prerequisites
    if fresh_virtualenv:
        cfg.python.provisioner.prerequisites(cfg)

    # Plugins can define a 'venv_hook' function, to give them a
    # chance to do something with the virtual environment just
    # being provisioned (e.g. preparing the venv by adding pth
    # files or by adding packages with other installers like
    # easy_install).
    for plugin in cfg.spin.topo_plugins:
        plugin_module = cfg.loaded[plugin]
        hook = getattr(plugin_module, "venv_hook", None)
        if hook is not None:
            logging.debug(f"{plugin_module.__name__}.venv_hook()")
            hook(cfg)

    cfg.python.provisioner.lock(cfg)

    # Install packages required by the project ('requirements')
    for req in cfg.python.get("requirements", []):
        cfg.python.provisioner.add(interpolate1(req))

    # Install development packages required by the project ('devpackages')
    for pkgspec in cfg.python.get("devpackages", []):
        cfg.python.provisioner.add(interpolate1(pkgspec), True)

    # Install packages required by plugins used
    # ('<plugin>.requires.python')
    for plugin in cfg.spin.topo_plugins:
        plugin_module = cfg.loaded[plugin]
        for req in get_requires(plugin_module.defaults, "python"):
            cfg.python.provisioner.add(interpolate1(req))

    cfg.python.provisioner.lock_extras(cfg)
    cfg.python.provisioner.sync(cfg)


def cleanup(cfg):
    """Remove directories and files generated by the python plugin."""
    try:
        rmtree(cfg.python.venv)
    except Exception:  # pylint: disable=broad-exception-caught
        warn("cleanup: no Python interpreter installed")
