# AGENTS.md

**Commit:** fd98768 | **Branch:** master | **Stack:** Python 3.13 + Home Assistant ≥2024.4.0 (HACS custom integration)

## OVERVIEW

HACS custom integration `custom_areas` (domain id). Creates composite per-area summary sensors aggregating power / energy / temperature / humidity / motion / window / climate from existing HA entities. UI-configured via config_flow (no YAML). Event-driven (not polling). Single platform: `sensor`. Version 1.2.0. License Apache-2.0. Author `@DefinitelyADev`.

**"Vibe-coded"** per README — pragmatic, not enterprise. Abstractions appear after the 3rd sibling. Tests chase features.

## STRUCTURE

```
custom_components/custom_areas/   # the integration (all runtime code lives here)
├── __init__.py                   # async_setup_entry / unload / reload, device registration
├── sensor.py                     # 581 LOC — AreaSensorCoordinator + 6 sensor classes (THE codebase)
├── config_flow.py                # AreasConfigFlow — UI setup
├── const.py                      # DOMAIN + CONF_* keys + defaults (single source)
├── manifest.json                 # HA manifest (domain, version, iot_class=local_push)
├── strings.json + translations/  # i18n
└── tests/test_sensor.py          # pytest-asyncio + MagicMock(spec=HomeAssistant)
docs/                             # mkdocs site (api, examples, developer, rationale)
.github/workflows/ci.yml          # 3-cell matrix: HA 2024(py3.12), HA 2025/2026(py3.13)
check_all.py, validate.py, run_tests.py, run_mypy.sh   # local dev orchestrators
```

## WHERE TO LOOK

- **All sensor logic** → `sensor.py`. `AreaSensorCoordinator` orchestrates; `AreaSummarySensor` is the composite; `PowerSensor`/`EnergySensor`/`TemperatureSensor`/`HumiditySensor`/`ClimateTargetSensor` are individual passthroughs.
- **Adding a config option** → `const.py` (key) → `config_flow.py` (schema) → `sensor.py` (consume) → `strings.json` + `translations/en.json` (label) → `tests/test_sensor.py` (cover).
- **State priority** documented in `README.md` "State Logic" — motion ON > power > threshold > idle > unknown. Mirror this exactly in code changes.
- **Class naming**: production code uses `Area*`. `docs/developer.md` still references stale `Room*` names — **docs lag, code wins**.
- **HACS / repo URLs**: `manifest.json` `documentation`/`issue_tracker` still point at legacy `room-entity` repo. Leave alone unless explicitly asked.

## CONVENTIONS

- **Formatter**: `black` line-length **120** (not 88). `isort` profile=black. Both enforced via `pyproject.toml` + pre-commit + CI.
- **Lint**: `flake8` max-line-length 120, ignore `E203,W503`. Also `ruff` + `mypy` + `pyright` (basic mode) — all must pass.
- **Async everywhere**. HA APIs are async-first; never block the event loop. Use `async_*` HA helpers.
- **Logging**: `_LOGGER = logging.getLogger(__name__)` at module top. Use `%s` lazy format — never f-strings in log calls.
- **Event-driven updates**: subscribe to source-entity state changes via HA event bus. **No polling**, no `scan_interval`.
- **Config keys**: defined ONCE in `const.py` as `CONF_*` constants. Never inline string keys in `config_flow.py` / `sensor.py`.
- **Tests**: `pytest-asyncio` + `pytest-homeassistant-custom-component`. Mock with `MagicMock(spec=HomeAssistant)`. Coverage with branch coverage (`--cov-branch`).
- **Type hints required** on public functions (pyright basic enforces).

## ANTI-PATTERNS (do not do)

- **Don't add YAML config**. UI/config_flow only.
- **Don't introduce polling** (`SCAN_INTERVAL`, `DataUpdateCoordinator` polling mode). Coordinator here is push-driven.
- **Don't rename `Area*` → `Room*`** to "match the docs". Docs are stale; PR-fixing the docs is fine, but don't drag the code backward.
- **Don't break the 120-col line limit** to match upstream HA's 88.
- **Don't catch `Exception` then swallow** — `__init__.py` deliberately re-raises as `ConfigEntryNotReady`. Preserve that.
- **Don't add new dev tooling** — black/isort/flake8/mypy/pyright/ruff already overlap. Pick the one that fires; don't add a 7th.
- **Don't bump HA min version** without checking the CI matrix (`2024.4.0` is the floor; matrix tests 2024/2025/2026).

## UNIQUE STYLES

- **Dual-form attributes**: every numeric attribute ships as both `_<unit>` (numeric, e.g. `power_w`) AND a stringified `<name>` with unit (`power: "28.6 W"`). When adding a new numeric attribute, ship both forms — this is the public contract per `README.md`.
- **Icon as state-derived attribute** on the summary sensor: `mdi:window-open-variant` > `mdi:motion-sensor` > `mdi:home`. Logic lives in `sensor.py`, default in `const.py` (`ICON_*` + `DEFAULT_ICON = "mdi:texture-box"`).
- **Active threshold default 50.0 W** (`CONF_ACTIVE_THRESHOLD` / `DEFAULT_ACTIVE_THRESHOLD`). Change carefully — user-visible default.
- **Device registry entry per area** is created in `async_setup_entry` (not deferred to platform setup) — keeps device visible even if sensor setup later fails.

## COMMANDS

```bash
python check_all.py                              # full gate: validate + tests + pyright + black + isort + flake8 + pre-commit
python validate.py                               # custom manifest/translations/structure checks
python run_tests.py                              # pytest with branch coverage → coverage.xml
./run_mypy.sh                                    # mypy only
pre-commit run --all-files                       # same hooks CI runs
black custom_components/custom_areas/            # apply formatting (line-length 120)
isort custom_components/custom_areas/            # apply import sort
```

CI runs `check_all.py` equivalent across the 3-cell HA matrix in `.github/workflows/ci.yml`.

## NOTES

- HACS install path in README points to repo `DefinitelyADev/room-entity` — legacy slug. Real repo is `custom-areas-integration`. Don't "fix" without confirming.
- `docs/developer.md` documents `Room*` classes that no longer exist. Treat as a known gap, not a contract.
- `pyproject.toml` configures black/isort/mypy only; flake8 reads `.flake8`; pyright reads `pyrightconfig.json`. Three config homes — check the right one when tuning rules.
- Tests live INSIDE the integration package (`custom_components/custom_areas/tests/`), not at repo root. Coverage targets the package via `run_tests.py`.
- `iot_class: local_push` in `manifest.json` is correct — integration reacts to HA state changes, no network I/O.
