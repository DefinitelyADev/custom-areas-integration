# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

The detailed knowledge base lives in [`AGENTS.md`](AGENTS.md) — read it on first task in a new session. This file is the quick-reference cover sheet; AGENTS.md has the full "where to look" map, anti-patterns, and stale-spot warnings. Keep both in sync when conventions change.

## Project shape

HACS custom integration `custom_areas` for Home Assistant ≥ 2024.4.0 (Python 3.13). Creates one composite summary sensor per area, aggregating power / energy / temperature / humidity / motion / window / climate from existing HA entities. UI-only config (`config_flow`), event-driven (no polling), single `sensor` platform. Version 1.2.0, Apache-2.0.

All runtime code lives in `custom_components/custom_areas/`. `sensor.py` (~580 LOC) is the bulk of the codebase: `AreaSensorCoordinator` orchestrates and `AreaSummarySensor` + five passthrough sensors (Power/Energy/Temperature/Humidity/ClimateTarget) hang off it. `const.py` is the single source of truth for `CONF_*` config keys — never inline string keys elsewhere.

When adding a config option, touch in this order: `const.py` → `config_flow.py` → `sensor.py` → `strings.json` + `translations/en.json` → `tests/test_sensor.py`.

## Commands

```bash
python check_all.py        # full local gate: validate + tests + pyright + black + isort + flake8 + pre-commit
python validate.py         # manifest / translations / structure checks
python run_tests.py        # pytest with branch coverage → coverage.xml
./run_mypy.sh              # mypy (must run from project root; script cd's into custom_components/)
pre-commit run --all-files # same hooks CI runs
```

Single test: `pytest custom_components/custom_areas/tests/test_sensor.py::TestClass::test_name -v`

CI runs a 3-cell matrix (HA 2024/py3.12, HA 2025/py3.13, HA 2026/py3.13) in `.github/workflows/ci.yml`, each pinning a specific `pytest-homeassistant-custom-component` version. Don't bump the HA floor (`2024.4.0` in `manifest.json`) without updating the matrix.

## Non-obvious conventions

- Line length **120** everywhere (black, flake8, isort) — not 88. Three config homes: `pyproject.toml` (black/isort/mypy), `.flake8` (flake8), `pyrightconfig.json` (pyright). Check the right file when tuning rules.
- **Event-driven only.** Subscribe via `async_track_state_change_event`. No polling, no `SCAN_INTERVAL`, no `DataUpdateCoordinator` polling mode.
- **Dual-form numeric attributes** on `AreaSummarySensor`: every numeric ships as both `_<unit>` numeric (`power_w`) and `<name>` stringified-with-unit (`power: "28.6 W"`). Ship both when adding a new numeric attribute — it's the public contract per README.
- **State priority** (mirror exactly): motion ON → `active`; else power > `CONF_ACTIVE_THRESHOLD` (default 50.0 W) → `active`; else any core entity configured → `idle`; else `unknown`.
- Logging: `_LOGGER = logging.getLogger(__name__)` at module top; `%s` lazy format — never f-strings in log calls.
- `__init__.py` deliberately re-raises setup errors as `ConfigEntryNotReady`. Preserve that.
- Tests live INSIDE the package (`custom_components/custom_areas/tests/`), not at repo root. Mock HA with `MagicMock(spec=HomeAssistant)`.

## Don't

- Don't add YAML config (UI/`config_flow` only) or polling.
- Don't rename `Area*` → `Room*` to "match" `docs/developer.md` — docs are stale, code wins. Fixing the docs is welcome; reverting the code isn't.
- Don't "fix" the legacy `DefinitelyADev/room-entity` URLs in `manifest.json` and the README HACS section — they look like typos but they're intentional aliases. Confirm before changing.
- Don't add a 7th linter/formatter. black + isort + flake8 + ruff + mypy + pyright already overlap; pick the one that fires.
- Don't swallow `Exception` in `__init__.py` — the `ConfigEntryNotReady` re-raise is deliberate.
