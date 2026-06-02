# Contributing

Thanks for your interest in improving **Custom Areas Integration**! Contributions
of all sizes are welcome — bug reports, docs, tests, and code.

This project is "vibe coded" (see the [README](README.md)), which mostly means:
keep it useful, keep it tested, and don't be precious about it. PRs that make it
better are always welcome.

## Ways to contribute

- 🐛 **Report a bug** — open an [issue](https://github.com/DefinitelyADev/custom-areas-integration/issues/new/choose)
- 💡 **Request a feature** — open an [issue](https://github.com/DefinitelyADev/custom-areas-integration/issues/new/choose)
- 🙋 **Ask a question** — use [Discussions](https://github.com/DefinitelyADev/custom-areas-integration/discussions)
- 🔧 **Send a fix or feature** — open a pull request (see below)

## Development setup

Requires **Python 3.13+** (the project targets Home Assistant ≥ 2024.4.0).

```bash
git clone https://github.com/DefinitelyADev/custom-areas-integration.git
cd custom-areas-integration
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pre-commit install
```

## Before you open a PR

Run the full local gate — it mirrors what CI checks:

```bash
python check_all.py
```

Or run the pieces individually:

| Command                        | What it does                              |
| ------------------------------ | ----------------------------------------- |
| `python run_tests.py`          | pytest with branch coverage               |
| `python validate.py`           | manifest / translations / structure checks |
| `./run_mypy.sh`                | mypy (run from the project root)          |
| `pre-commit run --all-files`   | the same hooks CI runs                     |

Run a single test:

```bash
pytest custom_components/custom_areas/tests/test_sensor.py::TestClass::test_name -v
```

## Conventions

- **Line length is 120** everywhere (black, isort, flake8) — not 88.
- **Event-driven only** — subscribe with `async_track_state_change_event`; no
  polling, no `SCAN_INTERVAL`.
- **UI configuration only** — config flow, never YAML.
- Config keys live in `const.py` (the single source of truth) — never inline
  string keys elsewhere.
- When adding a config option, touch files in this order:
  `const.py` → `config_flow.py` → `sensor.py` → `strings.json` +
  `translations/en.json` → `tests/test_sensor.py`.
- Tests live **inside** the package, in `custom_components/custom_areas/tests/`.

See the [Developer Guide](docs/developer.md) for architecture details.

## Pull request process

1. Fork the repo (or branch, if you have access) and create a topic branch.
2. Make your change, with tests and docs where it makes sense.
3. Make sure `python check_all.py` passes locally.
4. Open a PR against `master`. All status checks must pass before it can merge.
5. PRs are merged with **squash** or **rebase** (no merge commits), and the
   branch is kept up to date with `master` first.

By contributing, you agree that your contributions will be licensed under the
[Apache License 2.0](LICENSE), and that you'll follow the
[Code of Conduct](CODE_OF_CONDUCT.md).
