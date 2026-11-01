# Round 8 — Local-first data and personal exploration

## Plan versus delivery

| Phase | Status | Notes |
|---|---|---|
| 1 Local data layer | **Done, tested** | IndexedDB v2 (`finds`, `photos`, `meta`), schema version, one-time copy from localStorage (old copy kept), transactional saves, timestamps, photo size option and ordering. See `DATA_ARCHITECTURE.md` |
| 1.3 Data center | **Done, tested** | Counts, sizes, storage, last backup, schema, migration, reminder, orphan cleanup, media-cache clear, wipe with explicit tick |
| 2 Backup and recovery | **Done, tested** | Backup v4 with settings and learning; validated import with preview, conflict choice and failure-safe order; CSV kept. See `BACKUP_FORMAT.md` |
| 3 My Mushroom Life | **Done, tested** | 我的物种 (seen / self-judged / expert only with a named verifier), 再次探索 by place, 我的照片 with filters, year report (days, species, first-time species, regions, photos) and a share picture without places, coordinates or photos |
| 4 Seasonal intelligence | **Done, tested** | 季节情报 by region and month (filter: ground / wood / grass) with habitat, look-alikes, sample size, years, update date. Monthly refresh workflow (`seasonality.yml`) |
| 4.2 Forest type / trees / elevation filters | **Not done** | No structured, sourced data for every species; the habitat text is shown instead and the page says so |
| 5 Identification UX | **Done, tested** | Missing-information alarm (菌盖下面 / 菌托), unanswered items with why and jump buttons, kept-despite and unconfirmed per candidate, links to comparisons; no scores or probabilities |
| 6 Personal learning | **Partly** | Progress, wrong-answer book and seen species existed. **Not done:** quizzes from the person's own photos. Most journal photos carry the person's own guess, so quizzing on them could train a wrong identification. Revisit if expert-confirmed photos become common |
| 7 PWA and offline | **Done (automated)** | Offline cold reload, catalog and photos offline, offline record with photo, cache wipe keeps journal, update toast, storage display. **Not done:** real iPhone / Android tests |
| 8 UI polish | **Partly** | Empty states with next steps for journal, species, places, photos, season card; no new tab, no new navigation level |

## Tests

- `python3 tests/test_site.py`: **206 / 206**. Round 8 added 25 checks:
  - migration;
  - preview and cancel;
  - conflict keep and replace;
  - backup format;
  - data center;
  - orphan cleanup;
  - wipe;
  - my species, revisit, year report, share picture, photo empty state;
  - season intelligence and its empty state;
  - finder alarm and comparison links;
  - offline record with photo;
  - journal surviving a cache wipe.
- axe-core WCAG 2.2 AA:
  - views: journal (with records), 拾菌, finder (with an answer);
  - sizes and themes: 375 and 1440 px, light and dark;
  - result: 0 violations, no horizontal overflow.

## Device tests

**None on real devices.** All tests ran in headless Chromium. Still needed:
- **iPhone Safari and Home Screen app:**
  - IndexedDB migration on first open after the update;
  - photo picking at 12–48 MP (memory);
  - offline start in airplane mode;
  - GPS permission denied;
  - storage pressure.
- **Android Chrome:** the same, plus install and update.
- **Desktop Safari:** IndexedDB in private windows (expect the "cannot save" message).

## Open issues

1. Real-device testing (above).
2. Safari can evict a site's storage after about 7 days without a visit unless it is on the Home Screen. The app cannot
   prevent this; the backup reminder is the mitigation.
3. Photos are stored shrunk (max 2048 px); originals are not kept.
4. The monthly data workflow has not run yet. Its first run needs the repository's Actions to allow write access
   (Settings › Actions › Workflow permissions) for the commit, the Pages dispatch and the failure issue.
5. Forest type, associated-tree and elevation filters wait for sourced, structured data.
6. Personal photo quizzes are deferred (see Phase 6).
7. Some book-derived look-alike notes are thin; for example, 蜜环菌 does not name the deadly *Galerina marginata*. This
   needs a sourced content pass.
8. All safety open issues from `OPEN_ISSUES.md` still apply. No mycologist has reviewed the content.
