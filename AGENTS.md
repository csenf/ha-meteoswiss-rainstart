# MeteoSwiss Rain-Start

## [SOURCES]
- Concept: `docs/what/meteoswiss_rainstart_concept.md`
- Plans: `docs/how/`
- Changelog: `docs/changelog.md`

## [CONVENTIONS]
- Documentation: plain English.
- Testing: TDD.
- Code: DRY, SOLID, KISS, DDD.
- Keep changes focused.

## [COMMITS]
- Format: `<type>(<scope>): <description>`.
- Types: `feat`, `fix`, `perf`, `docs`, `style`, `refactor`, `test`,
  `chore`, `ci`.
- Reference issues: `Refs: #123`.
- Breaking change: `type!:` or `BREAKING CHANGE:`.

## [RELEASES]
- Use SemVer tags: `vMAJOR.MINOR.PATCH`.
- `BREAKING CHANGE` / `!:` → major.
- `feat` → minor.
- `fix` / `perf` → patch.
- Other types → no release.
- GitHub is the public release source of truth (tag + Release + stamped
  `manifest.json`). Gitea holds full history and local Ansible deploys.
- Develop on Gitea `main`. Promote with the Gitea workflow `Promote to GitHub`
  (SSH deploy key secret `GH_DEPLOY_KEY`). That job waits, then pulls the
  public GitHub repo back (HTTPS, no token) so a stamped release commit
  and tag land on Gitea.
- GitHub Actions runs `scripts/ci-tag-release.sh` on `main` and publishes
  a Release. It does not push to Gitea.
- Gitea Actions must not run `scripts/ci-tag-release.sh`.
- Do not commit `VERSION`. Ansible / `scripts/deploy.sh` may stamp a
  local-only `x.y.z+dev.gSHA` from `scripts/dev-version.sh` onto the HA copy.

## [BRANCHES]
- Use `feature/<issue-description>`, `fix/<issue-description>`, or
  `chore/<issue-description>`.
