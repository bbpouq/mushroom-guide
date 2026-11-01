# Local data architecture (round 8)

Everything a person creates stays in their own browser. Nothing is uploaded, and there is no account or server.

## Starting point (audit, before round 8)

| Data | Where it was | Problem |
|---|---|---|
| Journal records | `localStorage["mushroom-guide:finds:v1"]`, one JSON array | ~5 MB limit; every save rewrote the whole array; no timestamps |
| Photos | IndexedDB `mushroom-guide` v1, store `photos`, key → JPEG Blob | Fine; kept |
| Learning progress | `localStorage["mushroom-guide:learn:v1"]` | Small; kept |
| Settings | `localStorage` `mushroom-guide:field`, `:region`, `:recent`, `:today-h:*` | Small; kept |

Records already used stable ids (`Date.now()`) and the stable species slug (`sp`), never display names or array positions.
So the views could stay as they were. Only the two storage functions `findsLoad()` and `findsSave()` changed behind them.

## Now

IndexedDB database `mushroom-guide`, version 2 (`DB_VERSION`), schema version 2 (`SCHEMA_VERSION`):

| Store | Key | Holds |
|---|---|---|
| `finds` | `id` (keyPath) | JournalEntry records |
| `photos` | photo id (string) | PhotoAsset: a JPEG Blob |
| `meta` | name | `migration` (status, date, count), `schema`, `lastBackup` (date, counts, coordinate precision) |

### JournalEntry fields

The plan's names are mapped to the existing ones, which are kept for compatibility:

| Plan name | Field | Notes |
|---|---|---|
| id | `id` | number (old records) or string; never reused |
| speciesId | `sp` | species slug; `""` when not identified, then `other` holds the person's own name |
| identificationStatus | `status` | `none` / `candidate` / `expert` |
| observedAt | `date` | `YYYY-MM-DD` |
| location | `lat`, `lon`, `alt`, `acc`, `fuzzy`, `place` | read only when the person taps 记下当前位置; `fuzzy` = cut to 0.01° |
| habitat | `hab` | |
| nearbyTrees | `trees` | |
| photos | `photos` (ordered ids), `parts` (id → part shown) | Blobs live in the `photos` store |
| notes | `notes` | |
| confirmation | `verifier`, `vorg`, `vdate`, `vmethod` | the person's own note; the site cannot verify it |
| createdAt / updatedAt | `createdAt`, `updatedAt` | ISO 8601; added in round 8 |

### How saving works

- At start the records are read once into memory (`FINDS`).
- `findsSave(list)` compares `list` with `FINDS` and writes the added, changed and removed records in **one** IndexedDB
  transaction.
- `FINDS` is replaced only after that transaction commits, so a failed save (quota, blocked storage) changes nothing.
  The caller then says so.
- New or changed records get `updatedAt`. `createdAt` is kept, or taken from an old numeric id.
- If IndexedDB cannot be opened (some private modes, sandboxed previews), the app falls back to the old `localStorage`
  key. If that is blocked too, it says the journal cannot be used there.

### Photos

- Photos are shrunk on the device before they are stored: 标准 = long side 1280 px, 高清 = 2048 px, JPEG quality 0.82.
  The person picks the size in the form.
- Original files are not kept: on iPhone, a 12–48 MP original per photo would fill browser storage quickly.
- Photos can be reordered and removed.
- Deleting a record deletes its photos, and only after the record is gone.
- Photos added to a form that is never saved become "orphans"; the data center finds and removes them.

## Migration from version 1

Runs once, at the first start of round 8 code (when `meta.migration` is missing):

1. Read `localStorage["mushroom-guide:finds:v1"]`.
2. If it cannot be parsed, record `migration = {status: "failed", note}` and **leave the old value untouched**.
3. Otherwise give every record `createdAt`/`updatedAt`. A record without an id gets one, and duplicate ids are renamed,
   never dropped. Then write all records and the `migration` entry in one transaction.
4. The old `localStorage` value is **not deleted**. The data center shows it as 旧版副本. Only 清空本地数据 removes it.

Test coverage:
- a v1-shaped record is migrated with its timestamp and the old copy stays byte-identical;
- the whole existing suite runs on the new layer.

## Data center (菌记 › 数据管理)

It shows:
- records, photos and their size, orphan photos;
- browser storage use and quota, and whether long-term storage was granted;
- last full backup, schema version, storage engine, migration status and the old copy.

It offers:
- full backup and CSV export;
- import with a preview;
- orphan photo cleanup, after a confirm;
- clearing downloaded example images (the media cache only);
- clearing all records and photos (needs an explicit tick).

A reminder appears while there are records that are not in a full backup yet.
