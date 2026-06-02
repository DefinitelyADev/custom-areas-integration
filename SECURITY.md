# Security Policy

## Supported Versions

`custom_areas` is a Home Assistant custom integration distributed through HACS.
Security fixes are applied to the latest released version only — please update to
the newest release before reporting an issue.

| Version | Supported          |
| ------- | ------------------ |
| 1.2.x   | :white_check_mark: |
| < 1.2   | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues,
discussions, or pull requests.**

Instead, report them privately through GitHub's built-in vulnerability reporting:

➡️ **[Report a vulnerability](https://github.com/DefinitelyADev/custom-areas-integration/security/advisories/new)**

(You can also reach this from the repository's **Security** tab → **Advisories**
→ **Report a vulnerability**.)

Please include:

- A description of the vulnerability and its impact
- Steps to reproduce, or a proof of concept
- The integration version and Home Assistant version affected
- Any relevant logs, with personal data (entity IDs, tokens, locations) removed

## What to Expect

- I'll acknowledge your report as soon as I reasonably can.
- I'll confirm the issue and determine the affected versions.
- I'll work on a fix and release it, crediting you if you'd like.

This is a community project maintained in spare time, so response times are
best-effort — thank you for your patience and for helping keep it safe.

## Scope

This integration reads existing Home Assistant entity states and exposes
composite sensors. It has no cloud component, stores no credentials, and runs
entirely within your Home Assistant instance. The reports most relevant to this
project include:

- Unsafe handling of untrusted entity / attribute data
- Code that could crash or hang Home Assistant
- Exposure of sensitive data through sensor attributes or logs
- Vulnerabilities in the integration's dependencies
