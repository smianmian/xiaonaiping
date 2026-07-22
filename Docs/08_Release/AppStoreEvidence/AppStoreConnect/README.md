# App Store Connect Backfill Evidence

Store redacted App Store Connect page screenshots or PDFs for XiaoNaiPing draft-field backfill.

Use `../../APP_STORE_CONNECT_FILL_SHEET_20260630.md`, `../../APP_STORE_CONNECT_COPY_PASTE_20260630.md`, and `../../APP_STORE_SUBMISSION_PACKET.md` as the source of truth before taking screenshots or changing any field.

Use `EXECUTION_SHEET_20260630.md` during the live App Store Connect session. It is the step-by-step capture sheet for screenshot order, redaction, and non-replacement boundaries.

Required files after the draft is filled:

| File | Must show | Must hide |
| --- | --- | --- |
| `ASC-01-app-information.png` | App name, subtitle, Bundle ID, SKU, categories, copyright, privacy policy URL, support URL, terms URL | Apple ID email, phone, payment info, complete D-U-N-S |
| `ASC-02-version-information.png` | Version, selected build, description, keywords, release notes, screenshot order | tester emails, Apple ID email, verification codes |
| `ASC-03-pricing-availability-release.png` | Free price, China mainland availability, manual release setting | payment info, tax info, unrelated account data |
| `ASC-04-app-privacy.png` | Tracking=No and privacy-label data categories matching `APP_STORE_PRIVACY_LABEL.json` | Apple ID email, account private data |
| `ASC-05-age-rating.png` | Age-rating result, Kids Category not selected, vaccine/reminder answers match the release packet | Apple ID email, phone, payment info |
| `ASC-06-review-information.png` | Sign-in setting, review notes, contact fields completed, SMS/WeChat test instructions in private fields | verification codes, full phone numbers, recovery key, Apple ID email |
| `ASC-07-build-testflight-link.png` | Selected build and TestFlight processing status | tester emails, Apple ID email, internal notes |
| `ASC-08-submit-review-precheck.png` | Pre-submit page with no unresolved warnings | verification codes, full phone numbers, AppSecret, private keys |
| `ASC-PRIVACY-AGE-REVIEW-RESULT.template.json` | Template only; copy to `ASC-PRIVACY-AGE-REVIEW-RESULT.json` after ASC-04/05/06, privacy label, age-rating result, and review-account evidence are captured | no secrets should be filled in the template |
| `ASC-PRIVACY-AGE-REVIEW-RESULT.json` | Live privacy / age rating / review-information result with `captured-live-privacy-age-review`, ASC-04/05/06 checks, `04-privacy-label`, `17-age-rating-result`, `11-test-account-redacted`, redaction, answer-sheet matching, and post-result gates | recovery key, verification codes, full phone numbers, Apple ID email, contact phone, SMS/WeChat secrets, OBS AK/SK, AppSecret, payment/tax data, complete D-U-N-S |
| `ASC-BACKFILL-RESULT.template.json` | Template only; copy to `ASC-BACKFILL-RESULT.json` after the live App Store Connect session | no secrets should be filled in the template |
| `ASC-BACKFILL-RESULT.json` | Live backfill result with `status: captured-live-backfill`, `fieldEntryChecks` for every frozen draft field, `canSubmitAtCapture`, `screenshotFiles`, `redactionReviewed`, and the full XiaoNaiPing submission proof group | complete phone numbers, verification codes, recovery key, SMS/WeChat secrets, OBS AK/SK, AppSecret, Apple ID email, payment/tax data, complete D-U-N-S |

These files do not pass as final launch evidence by themselves. They only prove that App Store Connect fields were backfilled from the approved source documents. They do not replace company-account, filing, signing, TestFlight, final screenshot provenance, SMS provider, WeChat Open Platform, OBS, iOS 26.5 real-device, Live Activity, lock-screen, widget, privacy-label evidence, age-rating result evidence, or review-account evidence.

After screenshots are captured, freeze the fields. Fill `fieldEntryChecks` for App name, subtitle, description, keywords, category, age rating, privacy policy URL, support URL, terms URL, and review notes. Do not silently change description, keywords, release notes, screenshot order, privacy labels, age rating, review notes, selected build, price, availability, or release option. Any change must be recorded in `ASC-BACKFILL-RESULT.json`, the matching ASC screenshot must be recaptured, and the XiaoNaiPing App Store Connect, App Store evidence, TestFlight regression, production readiness, launch objective audit, provider evidence, mainland filing, and signed archive/TestFlight checks must be rerun before Submit for Review is considered.
