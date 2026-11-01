# Backup format

## Full backup (JSON), backupVersion 4

File name `拾菌记-完整备份-YYYY-MM-DD.json`:

```json
{
  "app": "mushroom-guide",
  "brand": "拾菌记 MycoTrail",
  "backupVersion": 4,
  "version": 4,
  "schemaVersion": 2,
  "exportedAt": "2026-11-01T18:00:00.000Z",
  "exported": "2026-11-01T18:00:00.000Z",
  "coords": "exact | approx | none",
  "finds": [ { "id": 1730000000000, "sp": "boletus-edulis", "date": "2026-10-01", "...": "JournalEntry fields", "createdAt": "…", "updatedAt": "…" } ],
  "photos": { "<photo id>": "data:image/jpeg;base64,…" },
  "prefs": { "mushroom-guide:field": "on", "mushroom-guide:region": "wa", "mushroom-guide:photo-q": "1280" },
  "learning": { "...": "the 学习 progress object" }
}
```

- `version` and `exported` repeat `backupVersion` and `exportedAt` so that older copies of the app can still read the file.
- `coords`: the person chooses exact, about 1 km or none. The app warns when exact coordinates leave the device.

## Reading backups

| File | Accepted |
|---|---|
| backupVersion / version 4, 3, 2, 1 | yes |
| a bare array of records (first version) | yes |
| version greater than 4 | no: "来自更新版本的拾菌记，请先更新页面" |

Import rules:

1. **Validate first.** The whole file is parsed and every record is checked (`findClean`): known fields only, right
   types, sane dates and coordinates.
2. **Photos only from embedded images.** A photo must be a `data:image/(jpeg|png|webp);base64` URI. A web address in a file
   is never fetched.
3. **Preview before writing.** The preview shows the records in the file, how many are new, identical, different
   (conflicts) or skipped, and the photo count. Nothing changes until 确认导入.
4. **Conflicts** are records with the same id but different content. The default keeps this device's version.
   Replacing happens only when that option is chosen.
5. **Settings and learning progress** are restored only when that box is ticked.
6. **Failure-safe order.** Photos are written first, then all records in one transaction. If saving the records fails,
   the photos just written are removed again and no record changes.

## CSV

`拾菌记-菌记-YYYY-MM-DD.csv` (UTF-8 with BOM, for Excel):
- Columns: 日期、菌名、学名、鉴定状态、确认人、确认机构、确认日期、确认方式、地点、纬度、经度、大概位置、海拔、生境、附近的树、照片数、备注.
- The same coordinate choice applies.
- CSV is for spreadsheets. It holds no photos and cannot be imported back: use the JSON backup to restore.
