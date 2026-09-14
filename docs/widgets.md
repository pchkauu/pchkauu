# Profile widgets

The README initially uses six local SVG snapshots in `assets/widgets/`: one light
and one dark version of each card. No external widget service is required.

## Update the local snapshots

Run from the repository root with Python 3.11 or newer:

```sh
python3 -m unittest discover -s tests -v
python3 scripts/update_profile.py
git diff --check
```

Only the Python standard library is needed. `GITHUB_TOKEN` is optional locally;
without it, GitHub's unauthenticated API rate limit applies. Never put a token in
the README, image URLs, command arguments, or tracked files.

`--output-dir <directory>` selects another destination. The script reads and
validates all API data before replacing any images. A failed request exits with
an error; it does not replace the existing snapshots with incomplete data.

## Data and appearance

- **Package map:** the five libraries listed in `PACKAGES`, grouped by purpose.
  The connecting line is not a dependency graph.
- **Version radar:** the numerically highest stable `MAJOR.MINOR.PATCH` tag, with
  an optional `v` prefix and build metadata. Prerelease tags are excluded. A
  matching published GitHub Release must be neither a draft nor a prerelease to
  receive the `Release` label. A repository without a stable tag shows
  `No stable tag`; a README version is never substituted for a tag.
- **Code footprint:** sums GitHub language byte counts across public repositories
  owned by `pchkauu`. Forks, archives, and `pchkauu/pchkauu` are excluded. Repositories
  with no language data contribute zero bytes but remain in the repository count.
  The five largest languages are shown separately, with any remainder under
  `Other`. Percentages are rounded to one decimal place.

Repository lists, tags, and releases are paginated. All cards show the UTC time
of their snapshot. Colors and layout live in `scripts/update_profile.py`.

## Connect GitHub Pages

Publication is a separate step from preparing the local files.

1. Publish the reviewed changes to `main`.
2. In **Settings → Pages → Build and deployment → Source**, select **GitHub Actions**.
3. In **Actions → Profile widgets**, choose **Run workflow** on `main`.
4. Confirm that `check`, `build`, and `deploy` succeed. Open all six published SVGs
   under `https://pchkauu.github.io/pchkauu/widgets/` and check the displayed snapshot
   time. For example:
   `https://pchkauu.github.io/pchkauu/widgets/package-map-dark.svg`.
5. Only after that verification, replace the nine `assets/widgets/` image-path
   prefixes in the README with `https://pchkauu.github.io/pchkauu/widgets/` and
   publish that README change. Keep the six local SVGs as recovery snapshots.

If the deployment reports a different base URL, use that confirmed URL in all
README image references.

The workflow validates pull requests without publishing. On `main`, it updates
and deploys after pushes, on manual runs, and daily at **04:17 UTC**. It publishes
a Pages artifact without committing image updates. `contents: read` is sufficient
for checks and API reads; only the deployment job receives `pages: write` and
`id-token: write`. No personal access token is required in Actions.

If a data request or check fails, deployment does not run and the last successful
Pages deployment remains available. Review failures in the Actions tab and rerun
the workflow after fixing their cause.

GitHub can delay scheduled runs and disables scheduled workflows in public
repositories after 60 days without repository activity. Re-enable the workflow
in Actions, then run it manually. The timestamp on each card helps identify old
data; GitHub's image proxy can also delay visible refreshes.

To use local snapshots again, replace the Pages prefix with `assets/widgets/` in
the README. The `<img>` in `<picture>` handles theme compatibility, not HTTP
failover: unavailable remote images do not automatically load the local copies.

References: [Pages workflows](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages),
[scheduled workflows](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule),
[language byte counts](https://docs.github.com/en/rest/repos/repos#list-repository-languages).
