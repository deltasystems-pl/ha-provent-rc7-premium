# Building a HACS-Compatible Release

1. **Update metadata**: confirm `custom_components/provent/manifest.json` and `hacs.json` reflect the latest version, filename, tags, and `icon` entries. `hacs.json` must include:
   * `content_in_root`: true
   * `zip_release`: true
   * `filename`: the exact ZIP asset name (`ha-provent-rc7-premium.zip`)
   * `icon`: `logo.png`
2. **Refresh documentation or assets** (logo, README, services, etc.).
3. **Generate the ZIP** from the repository root so the archive includes `hacs.json`, `README.md`, `FUTURE.md`, `LICENSE`, `logo.png`, and the entire `custom_components/` directory at the top level:
   ```bash
   cd /opt/app/rc7premium/ha-provent-rc7-premium
   zip -r ../ha-provent-rc7-premium.zip README.md RELEASE.md FUTURE.md LICENSE hacs.json logo.png custom_components
   ```
4. **Create or update a GitHub release** (e.g., `v1.0.0`, `v1.0.1`):
   * Attach the generated `ha-provent-rc7-premium.zip` as the release asset.
   * Keep the release `tag_name` consistent with version numbers in `hacs.json` and `manifest.json`.
5. **Point HACS at the release**: once the release is published, add or update the custom repository entry in HACS and choose the tagged release. HACS will now read `hacs.json` from the ZIP and install the integration with the provided icon and documentation.
