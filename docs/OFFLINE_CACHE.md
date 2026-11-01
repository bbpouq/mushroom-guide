# Offline and cache strategy

| What | Where | Strategy | Cleared by |
|---|---|---|---|
| App shell: `index.html`, manifest, icons | Cache Storage `mushroom-guide-vNN` (`CACHE` in `sw.js`) | Pre-cached at install. Pages are network-first, so updates arrive at once; the cached copy is used offline | Activating a new version deletes older `CACHE` names |
| Example photos, 3D library, Leaflet | Cache Storage `mushroom-guide-media-1` (`MEDIA`) | Cached on first use; every photo can be downloaded on request (离线使用) | Only 清除下载的示例图片, or a deliberate `MEDIA` bump |
| Records, photos, migration and backup metadata | IndexedDB `mushroom-guide` | Never touched by the service worker | Only the person (delete, wipe) or the browser's own data clearing |
| Settings, learning progress | `localStorage` | — | Same as above |

Updates:
- A new service worker installs only if every shell file downloads. If not, the old version stays in charge.
- It then takes over and deletes only old **shell** caches.
- When a new version takes over an open page, a toast says to reopen.
- A test wipes every Cache Storage entry and reloads. It checks that a record and photo written offline are still there.

Data updates: `.github/workflows/seasonality.yml` refreshes the public iNaturalist counts monthly.
- It writes only when every request succeeded, keeps a species' previous data if a lookup fails, and opens an issue on
  failure.
- It never touches anyone's journal; journals exist only on people's devices.

Limits:
- Browsers may evict storage under pressure. Safari also evicts script-written storage of sites not visited for about
  7 days, unless the site is added to the Home Screen.
- The app asks for persistent storage and shows whether it was granted, but the full backup is the only real protection.
