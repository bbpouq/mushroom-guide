# TASTES.md

## REJECT
- Never use red for anything but toxicity and emergency.
- Never let a photo, tint or glass effect compete with a safety warning for attention.
- Never put blur on cards or list rows; keep `backdrop-filter` for bars, sheets and toasts.
- Never use English eyebrows, thick rules, decorative numbering or web fonts.
- Never use amber `#D97706` as text; it is a fill, with black text on it.
- Never animate for decoration; motion only confirms a state change.

## REQUIRE
- Use iOS materials: translucent bars at `saturate(180%) blur(22px)` over a grouped background `#F2F2F7` / `#000`.
- Use the system font stack (SF Pro, PingFang SC) with large bold titles at `-0.02em` tracking.
- Use `0.5px` hairline separators and soft card depth `0 6px 20px rgba(0,0,0,.05)`; no card shadow in dark mode.
- Use filled capsules for chips and buttons; green `#15803D` (`#4ADE80` dark) marks the selected state.
- Maintain radii of `8px`, `12px`, `14px` and `22px`; sheets open from the bottom with a grabber on phones.
- Ensure every glass surface has an opaque fallback for reduced transparency.
- Write Chinese copy that is plain, calm and short.

## WHEN AMBIGUOUS
- Choose what an iOS system app would do; a warning should still be the loudest thing on screen.
- Orient toward: iOS Settings and Weather (Apple), natural-history field guides (print).
