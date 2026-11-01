# TASTES.md

## REJECT
- Never use red for anything but toxicity and emergency (`#B84D42` fill, `#A3392F` text).
- Never let a photo, tint or glass effect compete with a safety warning for attention.
- Never put blur on cards or list rows; keep `backdrop-filter` for bars, sheets and toasts.
- Never use English eyebrows, thick rules, decorative numbering or web fonts (a system serif for display titles is fine).
- Never use amber `#C18B43`, moss `#819477` or bark `#967A5A` as text; they are fills or drawings.
- Never let green read as a safety verdict: it marks interaction (selected, primary), not "safe" or "edible".
- Never fill the page with gradients or glass: the background aura stays barely visible (round 9, "Nature Editorial").
- Never animate a warning, look-alike note or the emergency page; motion must not compete with safety.

## REQUIRE
- Use iOS-style translucent bars at `saturate(160%) blur(22px)` over cream `#F8F6EF` (forest black `#0C0F0D` in dark mode).
- Use the system font stack (SF Pro, PingFang SC); page titles use the system serif (`--font-display`, Songti SC on Apple) for an editorial feel. Sizes come from `--fs-*` tokens.
- Use `0.5px` hairline separators and soft, warm card depth `0 6px 20px rgba(40,34,20,.06)`; no card shadow in dark mode.
- Use filled capsules for chips and buttons; forest `#3F6149` (`#9CCB9F` dark) marks the selected state; forest 900 `#243B30` for brand surfaces; moss `#819477` for quiet drawings. Text `#29352D`, secondary `#5E665D` (AA).
- Maintain radii of `8px`, `12px`, `14px` and `22px`; sheets open from the bottom with a grabber on phones.
- Use springy, physical motion (`cubic-bezier(.34,1.56,.64,1)`): press-to-shrink, pop-in, drag-to-dismiss.
- Ensure every glass surface has an opaque fallback, and every animation stops under reduced motion.
- Write Chinese copy that is plain, calm and short.

- Layer surfaces 1-3% apart in lightness (four layers); never pure black, never dark frames.
- Focus inputs with a deeper double ring, never an outline or border change.
- Drop every font weight by 40 in dark mode; lock numbers to tabular figures; let body text wrap "pretty".
- Fold with grid rows 0fr → 1fr; type titles in from a 6px blur (120ms, 30ms apart); drag on a 1200/80 spring, tap on 380/18.
- Show a check for 2.5s after copying, then put the icon back.

## WHEN AMBIGUOUS
- Choose what an iOS system app would do; a warning should still be the loudest thing on screen.
- Orient toward: natural-history museum field guides, Kinfolk-style nature editorial layouts and photography (print), iOS Settings and Weather (Apple). Photos attract, type organises, interaction helps finish the task.
