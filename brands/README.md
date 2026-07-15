# Home Assistant brand assets

Home Assistant shows an integration's logo (in **Settings → Devices & Services**, the
**Add Integration** search, and the device page) from the central
[`home-assistant/brands`](https://github.com/home-assistant/brands) repository —
**not** from this repo. Custom integrations have no local logo override, so until the
brand is submitted, HA shows a generic puzzle-piece icon.

This folder stages the assets ready for that one-time PR.

## Files (already sized to spec)

```
custom_integrations/provent/
├── icon.png       256×256   (square app icon)
├── icon@2x.png    512×512   (hDPI)
├── logo.png       256×48    (wordmark)
└── logo@2x.png    512×96    (hDPI)
```

All are PNG with transparent background. `@2x` files are exactly double their base.

## How to submit

1. Fork <https://github.com/home-assistant/brands>.
2. Copy this folder's `custom_integrations/provent/` into the fork's
   `custom_integrations/` directory (same path).
3. (Recommended) run the repo's image check locally, or just open the PR — its CI
   validates dimensions, transparency and optimization. If CI asks for smaller files,
   run them through `pngquant`/`optipng`.
4. Open the PR titled e.g. `Add provent (ProVent RC7 Premium)`.

Once merged, `https://brands.home-assistant.io/provent/icon.png` goes live and HA picks
up the logo automatically for every install — no integration change needed.

> The domain **must** be `provent` (matches `manifest.json`), and the folder is
> `custom_integrations/` (not `core_integrations/`) because this ships via HACS.
