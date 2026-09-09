# Synthetic demonstration

1. Generate the fixture with `scripts/generate_fixture.py` and inspect `fixtures/synthetic-case/manifest.json`.
2. Start the backend and frontend using the README commands.
3. Create case `DEMO-001`, set the analyst, and describe the input as synthetic.
4. Upload all 20 fixture JPEGs. Observe accepted and per-file failure counts.
5. Open `IMG-0005`; compare Summary, Metadata, and Raw tabs. Note that the Software tag is evidence of a tag only.
6. Open Timeline and Map. Confirm selected source, confidence, timezone status, derived-leg labels, and redacted coordinates.
7. Run analysis. Open the editing-software and rapid-transition findings and inspect their exact rules and support.
8. Acknowledge one finding with a qualified note and confirm its automated result remains visible.
9. Re-verify an evidence item and confirm its current hash matches the acquisition hash.
10. Generate a report from the completed run, preview it, download the PDF, and compare its displayed hash with the `.sha256` manifest.

The controlled mismatch test exists only in an isolated automated test directory. Production exposes no mutation action.

## Recorded walkthrough

With the local servers running, capture the browser walkthrough frames with:

```powershell
cd tests/e2e
npx playwright test demo-capture.spec.ts --project=chromium
cd ../..
.\apps\backend\.venv\Scripts\python.exe scripts\build_demo_gif.py work\demo-frames outputs\image-trace-demo.gif
```

The walkthrough covers the case registry, overview, evidence inventory, raw metadata, findings, privacy-safe route map, and versioned reports.
