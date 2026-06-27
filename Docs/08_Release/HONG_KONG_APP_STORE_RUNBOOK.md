# HONG_KONG_APP_STORE_RUNBOOK.md

## Status

- Project: 小奶瓶 / Baby growth record
- Date: 2026-06-18
- Target: Hong Kong App Store only
- Current conclusion: Hong Kong submission materials and `zh-Hant-HK` app resources are drafted, but the app is not submit-ready until production API, signing, TestFlight, App Store URLs, SMS, WeChat, copy review, screenshots, and remote proof are complete.

## App Store Connect Setup

1. Create or open the app record for bundle ID `com.mewpow.xiaonaiping`.
2. Set Pricing and Availability to Specific Countries or Regions.
3. Select only Hong Kong for the first release.
4. Set price to Free.
5. Use Lifestyle as the recommended primary category for V1.
6. Add Traditional Chinese metadata as the Hong Kong primary copy.
7. Add English (U.K.) metadata as the secondary copy if App Store Connect requires or benefits from it.
8. The app follows iOS system language and uses `zh-Hant-HK` resources when the device or per-app language is Traditional Chinese (Hong Kong).
9. Keep the China mainland / Hong Kong vaccine template switch visible inside the app; Hong Kong availability must not hide China mainland templates.

## Hong Kong Metadata

Use `Docs/08_Release/APP_STORE_METADATA.md` as the fill source.

Required copy already drafted:

1. App name: `小奶瓶`
2. Subtitle, Traditional Chinese: `溫柔記錄寶寶每一天`
3. Subtitle, English: `Gentle baby daily log`
4. Description, Traditional Chinese
5. Description, English
6. Keywords
7. Review Notes
8. Privacy label source JSON

## Required Before Submit

建议先执行统一发布核验入口（同一命令可复用于大陆提交）：

```bash
Backend/scripts/run_launch_readiness.sh \
  --env-file /srv/xiaonaiping/private/xiaonaiping-api.env \
  --base-url https://api.mewpow.com/xiaonaiping \
  --live-check
```

1. Configure Apple Developer Team in Xcode Signing & Capabilities.
2. Produce a signed iOS archive for App Store distribution.
3. Deploy production API to a real HTTPS domain.
4. Use the verified transitional URLs under `https://api.mewpow.com/xiaonaiping`, or replace them with the dedicated XiaoNaiPing API subdomain once DNS is ready.
5. Configure `XNP_API_BASE_URL` in the Release build.
6. Configure Huawei OBS or the approved production object store.
7. Configure SMS webhook provider for phone login.
8. Configure WeChat Open Platform and iOS OpenSDK.
9. Run `Backend/scripts/verify_remote_api.py` against production.
10. Run `Backend/scripts/verify_auth_providers.py --live-check` against production.
11. Run `Backend/scripts/check_diagnostics_redaction.py`.
12. Run `Backend/scripts/check_public_pages.py`.
13. Run `Backend/scripts/check_review_notes.py`.
14. Run `Backend/scripts/check_legal_drafts.py`.
15. Run `Backend/scripts/check_universal_links.py`.
16. Run `Backend/scripts/check_production_readiness.py` without `--allow-incomplete`.
17. Upload final App Store screenshots and archive evidence in `Docs/06_Release/PROOF_PACK.md`.
18. Complete TestFlight internal testing before review submission.
19. Human-review the generated `zh-Hant-HK` in-app copy before final screenshots and App Review submission.
20. QA the vaccine template region switch for China mainland and Hong Kong before final screenshots.

## Current Blocking Evidence

1. Production readiness is currently `ready=false`.
2. `xcodebuild archive` fails because no development team is configured.
3. App Store URLs currently use the verified `https://api.mewpow.com/xiaonaiping` transitional path; prefer a dedicated XiaoNaiPing API subdomain before final Hong Kong submission.
4. No remote production API proof exists.
5. SMS webhook and WeChat production credentials are not configured.
6. iOS WeChat OpenSDK is not configured.
7. `zh-Hant-HK` in-app localization is a first-pass generated draft and still needs human copy review.

## Official Apple References

1. App Store Connect availability: https://developer.apple.com/help/app-store-connect/manage-your-apps-availability/manage-availability-for-your-app-on-the-app-store
2. App privacy details: https://developer.apple.com/help/app-store-connect/manage-app-privacy/overview-of-app-privacy-details
3. Screenshot specifications: https://developer.apple.com/help/app-store-connect/reference/screenshot-specifications
