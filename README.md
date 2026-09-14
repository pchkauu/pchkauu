# Andrey Krasheninnikov

**Mobile & Backend Engineer · Flutter / Dart / Go**

I build mobile applications and backend services with clear contracts, predictable
async behavior, and useful diagnostics. I care about changes that are easy to
review, test, and ship.

### How I work

- **Architecture:** explicit ownership, small interfaces, and clear module boundaries.
- **Reliability:** typed errors, deliberate state transitions, and safe retries.
- **Diagnostics:** useful logs, observable failures, and enough context to find the cause.
- **Delivery:** focused reviews, meaningful tests, and verified releases.

### Open source

Small tools for the parts of an application that need to stay predictable.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/widgets/package-map-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/widgets/package-map-light.svg">
  <img src="assets/widgets/package-map-light.svg" alt="Package map: launch_mode for execution, package_context for boundaries, domain_error for outcomes, and observatory with talker_bloc_effects for diagnostics. Grouped by purpose, not dependencies." width="640">
</picture>

| Project | What it does |
| :--- | :--- |
| [observatory](https://github.com/pchkauu/observatory) | Isolate-aware Flutter logs, bounded history, safe HTTP logging, and Sentry incident capture. |
| [domain_error](https://github.com/pchkauu/domain_error) | Typed domain errors, Result/Either, and synchronous or asynchronous error capture. |
| [package_context](https://github.com/pchkauu/package_context) | Typed configuration and host dependencies with explicit package boundaries. |
| [launch_mode](https://github.com/pchkauu/launch_mode) | Foreground and background execution context for Flutter entry points and handlers. |
| [talker_bloc_effects](https://github.com/pchkauu/talker_bloc_effects) | One Talker observer for BLoC events, states, errors, and effects. |

### Version radar

The highest stable tag in each library. `Release` means that tag also has a
published, non-prerelease GitHub Release; otherwise it is marked `Tag`.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/widgets/version-radar-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/widgets/version-radar-light.svg">
  <img src="assets/widgets/version-radar-light.svg" alt="Stable versions of the five Dart and Flutter libraries, with separate Tag and Release labels. Open the project links above to inspect their tags and releases." width="640">
</picture>

### Code footprint

Language distribution by bytes of code in my public repositories, excluding
forks, archives, and this profile repository. The five largest languages appear
individually; the rest are grouped as `Other`. This describes the public code,
not time spent or proficiency.

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/widgets/code-footprint-dark.svg">
  <source media="(prefers-color-scheme: light)" srcset="assets/widgets/code-footprint-light.svg">
  <img src="assets/widgets/code-footprint-light.svg" alt="Language distribution across original, non-archived public repositories, measured in bytes of code. The card includes repository count and snapshot time." width="640">
</picture>

[Explore all public repositories](https://github.com/pchkauu?tab=repositories)

<sub>Each card shows its snapshot time. <a href="docs/widgets.md">Widget maintenance</a>.</sub>
