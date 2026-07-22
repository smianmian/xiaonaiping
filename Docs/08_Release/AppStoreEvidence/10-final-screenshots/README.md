# Final Screenshot Candidates

Date: 2026-06-28

These five screenshots are current iPhone 17 Pro Max / iOS 26.5 Debug simulator / iPhone 6.9" display candidates copied from `Docs/08_Release/Screenshots/`.

They were captured with screenshot seed data and production API URL injection so the account screenshot does not show `127.0.0.1`, tokens, real baby photos, or local debug infrastructure. `PROVENANCE.json` records the iOS 26.5 runtime, simulator UDID, Debug screenshot app path, build log, capture command, staging files, and final upload-order filenames.

These are current App Store screenshot candidates only. They are not TestFlight, signed-device, or Release build final evidence; final TestFlight / signed-build screenshots must still be archived before submission.

Final upload evidence must add `UPLOAD_PROVENANCE.json` in this directory. That file must use `evidenceType: final-app-store-upload`, name the install source as `TestFlight` or `Xcode 签名真机包`, bind the screenshots to `iPhone 6.9" display`, keep `device.runtime` at `iOS 26.5`, and list the five final upload files in order. Without that file, `Backend/proof/app-store-assets.json` and `Backend/proof/app-store-evidence.json` must remain incomplete.

The structured upload execution packet is `Docs/08_Release/FINAL_SCREENSHOT_UPLOAD_PACKET_20260630.json`. It is `upload-plan-not-evidence`: it locks the same-build, iOS 26.5, iPhone 6.9, redaction, stop-condition, and rerun rules, but does not replace `UPLOAD_PROVENANCE.json` or the final TestFlight / signed-device screenshots.

Run this before filling `UPLOAD_PROVENANCE.json` to capture the current file sizes, dimensions, and SHA-256 values without marking the evidence complete:

```bash
python3 Backend/scripts/inspect_final_screenshot_upload_files.py --output Backend/proof/final-screenshot-upload-file-metrics-20260630-current.json
```

Use `--require-complete` only after the iOS 26.5 TestFlight or Xcode signed physical-device upload provenance exists; before that, the command must stay incomplete.
