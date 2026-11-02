# v54.1 关于与反馈 (About & Feedback)

## What shipped

- **`#about` view** (alias `#contact`), with no tab, like the emergency page. It is reached from the footer links
  (关于与反馈 / 隐私 / 中毒急救) and from the settings sheet.
  - It opens with the safety callout: no identification, no edibility confirmation and no emergency advice here, plus a link to 中毒急救.
  - Then three report entries: 物种资料错误, 网站问题 and 功能建议.
  - Then the channels: GitHub Issues (a login is needed and reports are public), a contact email (「暂未提供」 until it is configured) and the source code.
  - Then 隐私 (`#about-privacy`) and 资料来源, both reusing what the site already says.
- **Report sheet** (`#report`, a `.bsheet` dialog):
  - It shows a form for the kind of report.
  - A read-only preview shows exactly the text that will leave the device.
  - Three buttons: **在 GitHub 打开（需要登录）**, **复制内容**, and the mail button.
- **Report button on every species sheet**, edible and toxic: 「这条资料有误？告诉我们」.
  - It prefills the species (Chinese and Latin name), the deep link (`#sp-` or `#tx-`) and the data version (`DATA.built`).
  - Error types: 形态描述 / 识别特征 / 有毒近似种 / 照片或授权 / 地区与季节 / 其他.
- **Honest status:** the site never says a report was submitted.
  - After GitHub opens, the note says 「要在那里登录并点提交才算发出；本站不知道你有没有提交。」
  - A blocked pop-up says so and points to copying the text.
  - Offline, the button explains that GitHub needs a network and offers copying.
- **Privacy**
  - A report contains only public species fields, the page link and what the person typed. Never the journal, locations, photos, settings or the user-agent string; the bug form offers a short, editable guess such as "iOS · Safari".
  - Text that looks like coordinates, a phone number or an e-mail address shows a warning before sending.

## Configuration (`FEEDBACK_CONFIG` in `src/template.html`)

```js
const FEEDBACK_CONFIG = { githubRepo: "bbpouq/mushroom-guide", issuesEnabled: true, contactEmail: "bbpouq@gmail.com", siteUrl: "https://bbpouq.github.io/mushroom-guide/" };
```

- `contactEmail`: the address the maintainer gave. With `null`, the mail button is disabled and reads 「邮箱暂未提供」, and the about page shows 暂未提供. Set an address to enable `mailto:`.
- `issuesEnabled: false`: the GitHub button is disabled and copying is offered instead.

## Still needed from the maintainer

1. ~~Contact email~~: set to bbpouq@gmail.com by the maintainer (2026-11-02). Setting it to `null` shows 「暂未提供」 again.
2. **Project introduction wording:** the lead on the about page is a placeholder written from CLAUDE.md. Replace it with your own words if you like.
3. **GitHub Issues settings**
   - Confirm Issues stay enabled on the repository.
   - Optionally add issue templates or labels (`资料`, `Bug`, `建议`). The titles start with `[资料]`, `[Bug]` and `[建议]`, so labels can be applied by hand or with a workflow.

## Tests (`tests/test_site.py`, "v54.1")

These tests cover:
- the footer, settings and `#contact` routes;
- the safety copy and the absence of a fabricated email;
- the species and toxic report prefill (names, deep link, version, error types);
- the coordinate and phone warning;
- that the GitHub URL contains no journal, location or user-agent data;
- that a GitHub window opens without any "submitted" claim;
- the blocked pop-up and offline notes;
- the mail button (enabled with the configured address, disabled 「暂未提供」 without one);
- Escape and keyboard Enter;
- 44px targets and no overflow at 320, 375, 390, 768 and 1024px, in normal mode and in outdoor + dark mode.

The `fingerprint.py` routes include `about` and `contact`, so the smoke and shadow tests cover them as well.

Screenshots are in `docs/v54_1/`: the about page and the report sheet at 375px light and dark, and at 1440px. "Before" is
simply the absence of the page: the old site had no about or feedback page.
