# Contributing

Thank you for considering making a contribution to this project. Any contribution
that helps us improve is valuable and much appreciated.

Do not hesitate to reach out by [email](mailto:contact@filigran.io) or on our
[Slack channel](https://community.filigran.io).

## How can you contribute?

Many contributions don't imply coding. Contributions can range from a suggestion
for improving documentation, requesting a new feature, reporting a bug, to
developing features or fixing bugs yourself.

* To report a bug or request a feature, open an issue using the provided
  templates.
* You can look through opened issues and help triage them (ask for more
  information, suggest workarounds, suggest labels, etc.).
* If you are interested in contributing code, fork the repository, create a
  branch, and open a pull request.

## Code quality and testing

In order to maintain a certain standard regarding code quality, this repository CI will run various tools against expectations:
- `isort` will be used to check for proper imports sorting, and the CI will fail if the checks fail
- `black` will be used to check for proper code formatting, and the CI will fail if the checks fail
- `flake8` will be used to check for proper code styling, and the CI will fail if the checks fail
- `pytest` will be used to run various levels of testing, and the CI will fail if the tests fail
- `coverage` with `codecov` will be used to check for proper code coverage, and the CI will fail if the level is below 80% for the current diff (a warning will be emitted if the level falls below 80% for the overall project)

<!-- filigran-conventions:start -->
## Commit, pull request & issue conventions

To keep the backlog consistent and searchable across all Filigran projects, this
repository follows a shared title and label convention. The full taxonomy lives
in [`.github/LABELS.md`](.github/LABELS.md). In short:

* **Titles** — All commit, pull request and issue titles follow the
  [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/)
  specification with a GitHub issue reference. PR title format (enforced by CI):
  ```
  type(scope?)!?: description (#123)
  ```
  - **type**: one of `feat`, `fix`, `chore`, `docs`, `style`, `refactor`, `perf`, `test`, `build`, `ci`, `revert`
  - **scope**: optional — use the affected module or area (e.g. `client`, `api`)
  - **description**: must start with a lowercase letter, no trailing period; preserve acronyms and proper nouns
  - **`(#123)`**: required — the linked issue number at the end
  - Examples: `feat(client): add bulk export endpoint (#42)`, `fix: resolve config loading issue (#99)`

* **No more bracket prefixes** — The old `[backend]` / `[frontend]` /
  `[component]` prefixes are **discontinued**; use a Conventional Commits scope
  instead (e.g. `fix(backend): ...`).

* **GitHub reference** — Pull request titles **must** end with the related issue
  reference, e.g. `(#1234)` (the PR title becomes the squash-merge commit). Every
  pull request must be linked to an issue. Enforcement is preventive and applied
  at the organization level; **Renovate** pull requests are exempt.

* **Signed commits** — All commits must be signed. See the
  [GitHub documentation on signing commits](https://docs.github.com/en/authentication/managing-commit-signature-verification/signing-commits).

* **Labels** — Every **issue** carries one primary type label matching its title
  prefix (`feature` for `feat:`, `bug` for `fix:`, `documentation` for `docs:`)
  plus optional area labels, and its GitHub **Type** (Feature / Bug / Task) set
  to match. **Pull requests carry a restricted label set** — exactly one
  ownership label (`filigran team` or `community`), optionally `vibe-coded` (an
  AI-assisted change the author reviews first), and the automatic language /
  `dependencies` labels. Type, area/scope and workflow labels are issue-only. Do
  not use the deprecated `enhancement` / `feature request` labels — use
  `feature`. See [`.github/LABELS.md`](.github/LABELS.md) for the shared palette
  ([`.github/labels.yml`](.github/labels.yml)).
<!-- filigran-conventions:end -->

## How can you get in touch for other questions?

If you need support or wish to engage a discussion about the project, feel free
to join us on our [Slack channel](https://community.filigran.io). You can also
send us an [email](mailto:contact@filigran.io).
