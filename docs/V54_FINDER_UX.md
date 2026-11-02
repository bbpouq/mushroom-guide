# v54 — 特征识别 (feature identification) UX

Scope: the PRD "MycoTrail v54 · 特征识别体验升级". It reworks the existing finder in place.
- Unchanged:
  - the five questions and their tags (`data/tags.py`);
  - the matching rules in `fmatch()` (toxic species matched leniently, edible strictly);
  - `fBestNext()`, the 3D model, routes, the data model and the journal schema.
- No new species, no images generated for identification, no score.

## Audit of v53.2 against the PRD

| PRD item | v53.2 | v54 |
|---|---|---|
| Short intro and 开始观察 | First question shown at once | Intro card (three lines) with 开始观察; shown again only when nothing has been answered |
| One question at a time, progress, edit | Already there (Sprint 3) | Kept; the progress dots now also show unknown answers |
| 没有 / 看不到 / 没检查 / 不确定 | Yes / no plus one "skip" | Every question has 不知道，跳过 (还没看) and 拿不准; 菌盖下面, 菌环 and 菌托 also have 看不到 with a reason. All three are stored as unknown (`funk`), never as "no" |
| Unknown never rules out a deadly species | Already true in `fmatch()` | Kept; the 信息不足 alert names the reason (e.g. 「“菌托”未观察（看不到：柄基没挖出来…）」) |
| Editable observation summary | Only "还没确认 N 项" chips | 你的观察: all five rows with value or unknown reason, a tip and 修改 |
| Evidence per candidate | 相符 / 仍列出 / 未确认 lines | Risk label (致命 / 有毒 / 外形候选 / 未评估) and counts 吻合 N · 冲突 N · 未知 N, then the lines 吻合 / 冲突，仍列出 / 关键待确认 (toxic) or 未知 (others) |
| Ranking | Toxic first, fixed order | Toxic first; within them deadly first, then fewer conflicts; otherwise the existing order. Stated as "排序只看危险程度和冲突多少，不计算匹配分数或概率" |
| Database limit | Callouts | Plus a final 「其他菌 / 本站没收录的种类：无法排除」 card in every result |
| No results / not enough information | Callouts | Kept; the empty state suggests 拿不准 instead of guessing |
| 返回补充关键观察 | Missing | Button to the first missing key question (菌托, then 菌盖下面); scrolls up and focuses the answers |
| 记录到菌记（未鉴定） | Missing | 记到菌记（未鉴定）: a new record named 未鉴定的菌, status 未鉴定, the observations in the notes. Never 候选 or 专家确认 |
| Session restore | 6 h in `localStorage`, unversioned | Versioned (`v: 2`) with unknown reasons and `started`. A v1 session migrates (skipped → 还没看); unreadable or invalid values start afresh. Never touches the journal |
| Back from a candidate | Worked (sheet over the view) | Kept and now tested: same answers, same results, same place |
| Screen readers | The whole result list was `aria-live` | A short live line (`#finder-live`) announces the counts; the list itself is no longer live |

## Safety copy

- The first block of every result is a danger callout:
  「这只是本站 86 种里的外形候选，不能确认是哪一种，也不判断能不能吃。没有列出的毒菌不代表安全…」, with the emergency link.
- 吻合 is a neutral pill, not a green check. Green stays for interaction (selected answers) only.
- The build now also fails on 「识别成功」「鉴定成功」「已鉴定」「可信度」「准确率」「放心采摘」「食用推荐」.
- Also removed: the extra `scroll-margin-top` on `#finder-results`. It added up with `scroll-padding-top`, so 查看候选 landed
  one header height too low.

## Tests

`tests/test_site.py`: the existing finder checks now click 开始观察 first (`fstart()`) and use the new words. New v54 checks:

- intro, and 开始观察 by keyboard;
- unknown kinds on every question;
- 看不到 stored as unknown, with deadly amanitas still listed;
- 冲突 on the card;
- risk ordering;
- no score or success wording, and the database-limit card;
- the live line;
- 修改 from the summary;
- 补充关键观察;
- back from a candidate;
- refresh, v1 migration and a broken session (with the journal untouched);
- 记到菌记 as 未鉴定;
- 320 / 375 / 390 / 768 / 1024 px, in normal and outdoor mode (dark): no overflow, 44 px buttons (52 px outdoors).

All in Playwright Chromium. No real phone, Safari or Firefox was used.
