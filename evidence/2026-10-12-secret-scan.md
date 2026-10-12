# Secret scan, 2026-10-12

- detect-secrets 1.5.0 over all tracked text files (npz, npy, vnnx, tflite excluded): 14 files with findings, every one a 'Hex High Entropy String' in evidence manifests, which are SHA-256 digests of artifacts (artifacts.json, compile.json, sim.json, dataset and export manifests, revisions.json, training.json). No key, token or password finding.
- git log -p --all grep for AWS, GitHub, OpenAI, Slack token shapes, private-key headers and API-key assignments: 0 hits.
- Tracked file names matching .env, secret, credential, .pem, .key, id_ed25519, id_rsa: none.
- Host names, user names, IP addresses and home paths: tools/check_pack.py scans every tracked text file on each run (PASS at the time of this scan).
