# Design — EasyWiki

Locked design system. All pages defer to this file.

## System
- Genre · modern-minimal
- Macrostructure · Long Document (single-page scroll, anchored nav)
- Theme · custom (vibe: "institutional clarity, paper-forward, trust")
- Axes · paper-band / editorial-display / indigo-accent

## Tokens (canonical)
```css
:root {
  --color-paper:      oklch(98% 0.005 250);
  --color-paper-2:    oklch(95% 0.008 250);
  --color-ink:        oklch(20% 0.02 250);
  --color-ink-2:      oklch(45% 0.015 250);
  --color-rule:       oklch(90% 0.01 250);
  --color-accent:     oklch(48% 0.18 265);
  --color-accent-ink: oklch(96% 0.02 265);
  --color-focus:      oklch(55% 0.15 265);

  --font-display: "Georgia", "Songti SC", serif;
  --font-body:    -apple-system, "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  --font-mono:    "SF Mono", "Fira Code", "Consolas", monospace;

  --ease-out: cubic-bezier(0.16, 1, 0.3, 1);
  --dur-fast: 180ms;  --dur-base: 240ms;  --dur-slow: 320ms;

  --radius-card: 4px;  --radius-pill: 999px;  --radius-input: 4px;
}
```

## CTA voice
- Primary · solid accent fill · 4px radius · 16px 40px padding
- Secondary · 1px ink-2 outline · 4px radius · transparent fill

## Motion stance
- Silent · fade-up on section enter · no decorative motion
- Reduced-motion fallback · opacity-only crossfade, 150ms.
