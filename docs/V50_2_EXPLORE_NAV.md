# v50.2 — 拾菌 navigation (v52)

拾菌 used to stack every big section one after another:
- 本月常见, 季节变化, 季节情报, the calendar;
- the six field-guide panels;
- the offline, appearance, outdoor-mode and install panels.

It now shows one sub-page at a time.

## Structure

| 分类 | 子页面 | Hash | Content (moved, unchanged) |
|---|---|---|---|
| 找菌 | 本月探索 | `#explore-now` | N 月在…常见 + 季节变化 (region chips above) |
| | 季节情报 | `#explore-intel` | 季节情报 |
| | 产季日历 | `#explore-cal` | 产季日历 (old `#guide-calendar`) |
| | 生境探索 | `#explore-hab` | habitat cards, taken out of the field guide (old `#guide-habitats`) |
| 野外指南 | 采集守则 | `#explore-rules` | 四条守则 (old `#guide-field`) |
| | 装备与准备 | `#explore-prep` | 带什么 + 什么时候找 |
| | 采集与观察 | `#explore-pick` | 采摘 + 做孢子印 |
| | 户外安全 | `#explore-safety` | 迷路或受伤 (S.T.O.P.) |
| 工具 | 离线下载 | `#explore-offline` | 这台设备上存了什么 + 装到手机桌面 (old `#guide-offline`) |
| | 户外模式 | `#explore-field` | the existing outdoor-mode panel and toggle |
| | 设置 | button | opens the Sprint 2 settings sheet; no copy of its logic |

The 外观 panel was removed from 拾菌 because the settings sheet already has it. The old `#guide-theme` link now opens the
settings sheet.

## Behaviour

- **Defaults:**
  - 拾菌 opens on 找菌 › 本月探索;
  - each category remembers its last sub-page (`xpLast`, in `sessionStorage`, so a refresh keeps it);
  - plain `#explore` (for example coming back from another tab) reopens the last sub-page and its scroll position.
- **Switching:**
  - a sub-page switch pushes `#explore-<sub>` (back and forward work) and scrolls to the top of the content (the navigation);
  - tapping the 拾菌 tab again goes to 找菌 › 本月探索 at the top.
- **Old links:** `#guide-*` ids open the pane that now holds them.
- **Hidden panes:**
  - they carry the `hidden` attribute, so they are not focusable or read out;
  - the selected category uses `aria-pressed`, the selected sub-page `aria-current="page"`;
  - the region chips show only where they change the content (本月探索, 季节情报, 产季日历).
- **Layout:** the categories are a segmented control and the sub-pages one equal-width row, with no nested scrolling tabs. The navigation is not sticky, so it takes no screen space while reading. It is capped at 720px wide on desktop and uses 52px targets in outdoor mode.
- **Bug found and fixed:** a 设置 button other than the header gear did nothing, because the listener was bound to the first button only. It is now delegated.

## Tests

- `tests/test_site.py`: **285 / 285** (19 new). The new checks cover:
  - default page;
  - one pane at a time;
  - page height;
  - per-category memory;
  - scroll to content;
  - back and forward;
  - refresh;
  - leaving and returning to the tab;
  - tab re-tap;
  - four old links and `#guide-theme`;
  - hidden panes out of the focus order;
  - every old section still reachable;
  - outdoor mode with dark theme;
  - no JS errors.

  Six older tests were pointed at the new hashes. Their checks are unchanged.
- **Height of 拾菌 at 375px:** about 700–3400px depending on the sub-page; it was the whole stack before.
- **axe-core WCAG 2.2 AA:**
  - every pane × 375/768/1440 × light/dark × outdoor mode (120 checks): 0 violations, no overflow, no JS errors;
  - the 120 view combinations: 0 violations.

  One real issue was fixed on the way: the desktop tab links were muted grey on the translucent header over photos (now full text colour).

## Not done

- Content trimming. Navigation first, as asked.
- Real-device testing (iPhone Safari and Home-Screen app, Android Chrome).
