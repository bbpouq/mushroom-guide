# CI / CD

Four layers. All use Playwright Chromium on GitHub-hosted Ubuntu runners; nothing here touches a person's journal data.

| Layer | Where | When | Fails on |
|---|---|---|---|
| Build and lint | `ci.yml` › Build and lint | every push (except docs-only) and every PR to `main` | `build_site.py` errors (design-system lint, safety rules, banned phrases), or `public/` not rebuilt before committing |
| Integration (end-to-end) | `ci.yml` › End-to-end tests | after the build | any check in `tests/test_site.py` (the full suite, ~370 checks; log uploaded as the `test-log` artifact) |
| Accessibility sweep | `ci.yml` › Accessibility sweep | after the build | any axe-core WCAG 2.2 AA violation or horizontal overflow (`tests/a11y_sweep.py`: every view, every 拾菌 sub-page and the finder's result states × 320/375/390/768/1024/1440 px × light/dark × outdoor mode) |
| Shadow test | `ci.yml` › Shadow test | after the build | this build vs the live site (`tests/shadow_diff.py`): differences are reported in the job summary; it fails only when this build lost a safety sentence or an emergency link, broke a deep link that works in production, or has a JavaScript error production does not have |
| Deploy | `pages.yml` | push to `main` | stale `public/index.html` |
| Smoke test | `smoke.yml` | after every successful deploy, daily at 15:43 UTC, or by hand | the live files not matching the deployed commit within 10 min, a deep link opening the wrong view, a missing safety sentence or emergency link, a JavaScript error, or the service worker not reporting 已可离线. Opens an issue on failure |

The shared checks (deep links → view, safety sentences, emergency links, catalogue sizes) live in `tests/fingerprint.py`.

## Running them locally

```sh
pip install playwright==1.64.1 pillow==12.3.0 && python3 -m playwright install chromium
python3 tests/test_site.py                       # full suite
npm install --no-save axe-core@4.14.0 && python3 tests/a11y_sweep.py --quick   # 375 and 1440 px only
python3 tests/shadow_diff.py                     # this checkout's public/ vs the live site
python3 tests/smoke_live.py --no-match           # the live site, without waiting for a matching deploy
```

## Notes

- CI runs on every branch, so a feature branch shows its result before it is merged; `main` is deployed by `pages.yml`
  whether or not CI passed. To make CI a gate, turn on branch protection for `main` with the four `CI` jobs as required
  checks (GitHub › Settings › Branches); that is a repository setting, not a file.
- Only Chromium is tested. WebKit (Safari) and Firefox could be added to the matrix later; real devices are not covered.
