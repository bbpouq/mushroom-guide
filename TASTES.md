# TASTES.md

## REJECT
- Never use red for anything but toxicity and emergency.
- Never let a photo, tint or glass effect compete with a safety warning for attention.
- Never put blur on cards or list rows; keep `backdrop-filter` for bars, sheets and toasts.
- Never use English eyebrows, thick rules, decorative numbering or web fonts.
- Never use amber `#C98A2B` as text; it is a fill, with black text on it.
- Never let green read as a safety verdict: it marks interaction (selected, primary), not "safe" or "edible".
- Never animate a warning, look-alike note or the emergency page; motion must not compete with safety.

## REQUIRE
- Use iOS-style translucent bars at `saturate(160%) blur(22px)` over warm ivory `#F5F2EA` (forest black `#0C0F0D` in dark mode).
- Use the system font stack (SF Pro, PingFang SC) with large bold titles at `-0.02em` tracking.
- Use `0.5px` hairline separators and soft, warm card depth `0 6px 20px rgba(40,34,20,.06)`; no card shadow in dark mode.
- Use filled capsules for chips and buttons; forest green `#2D5A3D` (`#9CCB9F` dark) marks the selected state; moss `#5E7334` for quiet drawings.
- Maintain radii of `8px`, `12px`, `14px` and `22px`; sheets open from the bottom with a grabber on phones.
- Use springy, physical motion (`cubic-bezier(.34,1.56,.64,1)`): press-to-shrink, pop-in, drag-to-dismiss.
- Ensure every glass surface has an opaque fallback, and every animation stops under reduced motion.
- Write Chinese copy that is plain, calm and short.

## WHEN AMBIGUOUS
- Choose what an iOS system app would do; a warning should still be the loudest thing on screen.
- Orient toward: natural-history museum field guides and nature photography (print), iOS Settings and Weather (Apple).
