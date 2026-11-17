# Actual-browser validation

From the repository root, in an environment permitting localhost sockets:

```sh
python -m pip install -e '.[studio,test,docs]'
(cd apps/studio && npm ci && npm run build)
npm install --prefix tests/e2e
(cd tests/e2e && npx playwright install --with-deps chromium)
python scripts/validate_release.py --checks browser,docs
```

The runner starts an isolated real service, executes the demo through the browser,
inspects alignment data, checks dark mode and a mobile viewport, then stops the
service. It records logs and a JSON report. No API responses are mocked. Missing
dependencies are blocked checks, never passing tests. Exit 2 means blocked;
exit 1 means a check ran and failed. The runner selects an available loopback port.
