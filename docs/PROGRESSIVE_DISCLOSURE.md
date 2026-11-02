# Content density and progressive disclosure (2026-11 PRD)

The rule used: delete duplicates, shorten, then decide where each piece belongs:
- **inline** (always visible): what a person must know before acting;
- **info button** (L1): one to three sentences explaining a term or a number;
- **fold** (`details`, L2): longer method or background;
- **link** (L3): the full reference.

Safety conclusions, emergency actions, irreversible consequences and privacy risks before an action are never placed
behind an info button.

## Phase 0: content safety (done first)

| Item | Change | Why |
|---|---|---|
| 醋渍 (vinegar pickle, kept 3 months) in 保存 | **Removed.** The 保存 panel now says the site gives no pickling, oil or canning methods, linking NCHFP ("Do not can wild mushrooms"). The build fails on the old recipe phrases. | A home-canned or pickled wild mushroom carries a botulism risk; the recipe was not from a tested source. |
| 「冷冻、腌制的宜在几个月内吃完」 | Changed to 「冷冻的宜在 3 个月内吃完」. | It implied that pickled wild mushrooms are a normal option. |
| Book note 「幼嫩者可煮熟后腌渍」 (one bolete) | Removed. | Same reason. |
| 菌孔 = 「海绵状」 (features list, glossary, 3D model note) | The pores are now described as many small holes, some so fine they look smooth. The glossary explains that bolete pore layers are soft and spongy, while polypores such as 硫磺菌 have fine pores (2–4 per mm, MushroomExpert, see `audit_log.py`). | "Spongy" sent people who had 硫磺菌 to the wrong answer (the v56 species audit fixed the same issue in the finder options). |

## Phase 1: shared component

`.info` (in `src/template.html`):
- a short visible line (`.info__line`) and a text button (`.info__btn`: an icon plus a label such as 识别器的局限 or 数据如何统计);
- the button toggles a region right below (`.info__pop`, `hidden` attribute, `aria-expanded` / `aria-controls`).

Behaviour:
- Click, tap, Enter or Space toggles it. Escape closes it and returns focus to the button. A click elsewhere closes it.
- Only one is open at a time, and none is open by default.
- It opens in place, so it can never leave the screen or float over another tab.
- The label is small, with a 44px hit area (`::after`). Outdoor mode uses 52px targets and body-size text.

JS helpers: `infoBtn(id, label)` and `infoPop(id, html)` for rendered content.
- No hover tooltips, no delayed pop-ups, no first-visit tutorials.
- The text stays in the DOM, so screen readers and copy can reach it.

## Phase 2: pilots

| Module | Visible (inline) | Behind the info button / fold | Measured at 375px (live before → after) |
|---|---|---|---|
| 特征识别 opening | Lead: 「按你看到的特征逐题回答，不确定就跳过。」 Warning: 「只列外形候选，不能确认是哪一种，也不判断能不能吃。结果里没有毒菌，不代表这朵没毒。」 Intro: two bullets. | **识别器的局限**: how many species the site covers, toxic first, unknowns never exclude a toxic species, mix-ups that need the volva or spore print. | Text before 开始观察: 254 → 148 characters (−42%). 开始观察 moves up 107px (757 → 650). |
| 季节情报 | The required sentence 「历史观察数据反映…实时出菇预测。」, once at the top, plus the per-chart data line (`obsSummary`: source, region, years, sample size, date). | **数据如何统计**: sampling bias, uploads vs abundance, monthly update, <30 = 样本不足. **怎么比较** in 三地对比: how the levels are computed. | Explanatory text: 334 → 119 characters (−64%). |
| 菌记 › 位置 | 「点按钮才读取定位，只存在这台设备上。」 next to the button. | **位置怎么存**: when location is read, 0.01° / ~1 km truncation, no altitude, the export precision choice and the risk of sharing exact coordinates. | Hint text in step 2: 90 → 29 characters (−68%). |

The export warning about exact coordinates is unchanged: it still appears at export time, before anything leaves the device.

## Phase 3 (partly done)

| Module | Change |
|---|---|
| 生境探索 | The cards start right away. One visible line says that habitat cannot identify a mushroom. **菌和树的关系** holds the saprobic and mycorrhizal intro and the "recommended species only" note. The repeated per-card note was removed. |
| 关于与反馈 | Report actions come first. 隐私 and 资料来源 are folds; `#about-privacy` opens its fold. |
| Not changed on purpose | 中毒急救 (every action stays visible); recipe safety tips and the exact kitchen sentence; the finder results callout; the 清空本地数据 confirmation; export warnings. |
| Still to do | The home safety note, the field-guide panels (规则 / 准备 / 采集), the 离线下载 explanation and the 菌记 鉴定状态 text. Each needs the same audit (what is a decision-time fact, what is background). They are left for a follow-up so that each can be reviewed on its own. |

## Tests

`tests/test_site.py` (PD) covers:
- **Phase 0:** no pickling recipe, the NCHFP link, the pore wording.
- **Safety lines visible:** with every explanation closed, the safety lines show in the finder, 季节情报, 生境 and 菌记 位置.
- **Keyboard:** Enter, Space, Escape with focus returned, click outside, one open at a time.
- **State kept:** finder answers and the region survive opening and closing an explanation.
- **About folds:** `#about-privacy` opens its fold.
- **Layout:** no overflow and on-screen panels with 44px hit areas at 320, 390 and 768px, in normal and outdoor + dark modes.

Existing tests for the 季节情报 bias text and the 生境 wording now open the explanation first.

Screenshots: `docs/pd/{finder,intel,gps}-{before,after}.png`. "Before" is the live site; "after" is this build; both are 375px, light mode.
