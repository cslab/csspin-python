# AGENTS.md

This file provides guidance to AI agents when working with code in this
repository.

## What this is

`csspin-python` is a plugin package for `csspin`, CONTACT Software's project
task runner. It bundles Python-related plugins (provisioning an interpreter and
virtualenv, running pytest/behave/playwright, building an SBOM) that `spin`
loads into a host project via its `spinfile.yaml`. This repo is itself
`spin`-provisioned, for its docs and for self-testing.

## Commands

```bash
uv venv                                # fresh clone only
uv pip install -r requirements-dev.txt # -e .[aws_auth,uv] plus csspin, pytest, mypy
uv run pytest tests/unit               # fast, mocks csspin, provisions nothing
uv run pytest tests/acceptance         # no -m marker, see below
uv run pytest tests/integration -m integration
uv run pytest tests/unit/test_python.py::test__configure_pipconf  # single test
prek run --all-files                   # quality gate
prek run mypy --all-files              # a single hook
```

The dev virtualenv lives at `.venv` (`uv run` ignores any other name).
`CONTRIBUTING.md` still documents `venv/`, which is what the repo's
`.gitignore` covers.

Do not use `uv sync`. `pyproject.toml` declares no dev dependencies, so
`csspin`, `pytest`, and `mypy` reach the environment only via
`requirements-dev.txt`, and `uv sync` prunes everything it does not know about.
CI installs the same file, but its jobs come from the shared
`pod/tools/spin_plugin_common` template and are not editable from here.

Bare `prek run` only looks at staged files and reports green on unstaged edits,
so always pass `--all-files` or `--files <paths>`. Run single linters through it
too, which pins the versions and arguments from `.pre-commit-config.yaml`.

Markers (`pyproject.toml`): `acceptance`, `integration`, `wip`. Acceptance and
integration tests both shell out to a real `spin` and provision real
interpreters under a temp dir, so both are slow and need network access. Only
the unit tests are hermetic (they mock `csspin`, hence the
`mock.patch("csspin.task")` import guard in `tests/unit/*`). Two traps:
`tests/acceptance/python_constraints` carries no `acceptance` marker, so
`-m acceptance` silently skips it; and several suites resolve spinfile paths
relative to the working directory, so pytest has to run from the repository
root.

## Architecture

### Plugin structure

Each module directly under `src/csspin_python/` is one independent `spin`
plugin, paired with a `<name>_schema.yaml`. Underscore-prefixed modules are not
plugins: `_predict_wheel_filename.py` is a script `python_sbom.py` runs in a
subprocess under the target project's own interpreter, so the version and
platform tags come out right.

There is no `__init__.py` under `src/`; `csspin_python` is a namespace package.
One consequence is that `pytest.py` collides with the real `pytest` inside
pylint's hook environment, which `pyproject.toml` works around with an `ignore`
entry and a `generated-members` declaration. Leave both as they are.

A plugin module is a flat set of module-level hooks and tasks that `spin` calls
by convention:

- `defaults = config(...)` — default config tree, merged into
  `cfg.<plugin_name>` and overridable from `spinfile.yaml` or `-p`. A nested
  `requires=config(python=[...], spin=[...])` declares pip packages to install
  and spin plugins to depend on (resolved into `cfg.spin.topo_plugins`).
- `configure(cfg)` — after config merge, before provisioning; adjust config,
  register requirements.
- `init(cfg)` — check that prerequisites already exist; runs on every `spin`
  invocation.
- `provision(cfg)` / `finalize_provision(cfg)` — the work behind
  `spin provision`.
- `venv_hook(cfg)` — optional, called by `python.py:venv_provision` on every
  plugin that defines it. Runs on every provision, not only on a fresh venv.
- `cleanup(cfg)` — undo `provision`, called by `spin cleanup`.
- `@task()` / `@task("name", when="test")` — becomes a `spin` subcommand
  (`spin pytest`, `spin python:wheel`).

A plugin's `defaults` is not the full set of properties it reads. `python.py`
uses `cfg.python.pipconf`, `constraints`, `extra_index_urls`, and several
`aws_auth.*` keys that only `python_schema.yaml` declares, with values coming
from `csspin`'s own defaults. Check the schema before concluding a key is
unset, and update it when adding properties: it also drives config validation
and the generated docs.

### Provisioning

`csspin_python.python` is the foundational plugin: it provisions the interpreter
(pyenv on Linux/macOS, nuget on Windows, or a pluggable `ProvisionerProtocol`)
and the project virtualenv, and registers `cfg.spin.subprocess_environment` so
every `csspin.sh()` call runs inside that venv. Most other plugins declare a
`requires.spin` dependency on it.

`ProvisionerProtocol` is the extension point for alternative strategies: assign
an instance to `cfg.python.provisioner` from another plugin's `configure()`.
`uv_provisioner.py` does that, swapping in a `SimpleUvProvisioner` that uses
`uv` for interpreters and packages; it needs the `uv` extra. Provisioners are
pickled into a memo file, so they must survive `pickle.dumps`.

Memoization is not a general install-skipping cache. `SimpleProvisioner.install`
always runs pip; its memo only decides whether to pass `--upgrade`. Two memos
do gate work: the provisioner memo, and the one guarding `python_sbom`'s
separate persistent `cyclonedx-bom` venv (recreated on a version mismatch,
and separate because `cyclonedx-bom` cannot be a dependency of this package).

### Package indexes and aws_auth

`python.py` writes the venv's pip config (`pip.conf`, `pip.ini` on Windows) and
the index URLs in it. Under `uv_provisioner` the same URLs are mirrored into the
venv's `uv.toml`, because `uv pip` ignores pip's config, so index-related
changes have to be made in both places.

With `python.aws_auth.enabled`, the primary index and each
`aws_auth.extra_indexes` entry are resolved into authenticated CONTACT
CodeArtifact URLs through `csaccess`, the optional `aws_auth` extra. That import
is lazy and `die()`s with a pointer to the extra, so the plugin still loads
without it. Token validity is memoized against the index base URL, and
credentials go into `csspin.secrets` to keep them out of logs.

### Activation script patching

`python.py` rewrites the venv's activation scripts for every supported shell
(the `ActivateScriptPatcher` subclasses) so that variables set via
`csspin.setenv()` during provisioning also apply when a user sources the script
outside of `spin`, and get reverted by a patched `deactivate`.

### Docs and tests

`doc/plugins/*.rst` documents each plugin; the `*_schemaref.rst` pages are
generated from the schemas by `spin schemadoc`, wired up as a `build_rules`
target in this repo's `spinfile.yaml`.

Tests split into `tests/unit/` (functions in isolation, `csspin` mocked),
`tests/acceptance/` (one plugin against a dummy project fixture or a bare
spinfile under `yamls/`), and `tests/integration/` (the real `spin` CLI against
the spinfiles in `tests/integration/yamls/`, provisioning under a temp
`spin.data` dir, driven by `provision_env()`). `test_aws_auth.py` skips without
`CS_AWS_OIDC_CLIENT_SECRET`. The session-scoped `disable_global_yaml` fixture in
`tests/conftest.py` keeps a developer's local `global.yaml` out of test runs.
