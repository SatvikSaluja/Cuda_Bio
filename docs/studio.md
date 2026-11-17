# WarpAlign Studio

Build the frontend and start the loopback API:

```sh
(cd apps/studio && npm ci && npm run build)
warpalign-studio --port 8000
```

Open http://localhost:8000. A release wheel built after the frontend includes its assets and can serve Studio outside the repository. `WARPALIGN_STUDIO_DIST` overrides the bundle location. Startup prints a missing-bundle diagnostic when necessary.

## Workspace

The overview reports actual backend connectivity and persistent history. **Try a real demo** submits synthetic sequences to the same worker used for uploads. New alignment supports drag-and-drop FASTA/FASTQ, input-order or identifier pairing, scoring, CPU threads, memory budget, timeouts, checkpointed traceback and heuristic retries.

Results search and sorting operate over the entire SQLite dataset, then paginate. Sequence payloads are fetched only when an alignment is opened. Completed results stream as JSONL or PAF. Jobs run in separate processes; cancellation terminates the process group, including a mapper subprocess on POSIX. Job deadlines enforce a wall-clock bound independently of CPU alignment deadlines.

The viewer indexes CIGAR runs, renders only visible bases, provides column/variant navigation and zoom, and includes an accessible text view. Dark/light appearance and alignment defaults are browser-local preferences.

## Persistence and cleanup

By default the service stores SQLite data under `~/.local/share/warpalign`. Set `WARPALIGN_DATA_DIR` to choose another directory. Results contain genomic sequences in plaintext on local disk. Clearing finished jobs removes their logical database rows; it is not a secure disk-erasure guarantee. Temporary job directories are removed after normal completion, failure or cancellation. A hard system crash can leave temporary directories for manual cleanup.

On restart, unfinished jobs become `interrupted`. Only one POSIX service may own a data directory. Jobs are not automatically resumed. The upload limit is 32 MiB and at most four alignment jobs may be queued/running. Benchmarks are serialized and reject requests while alignment jobs are active.

The unauthenticated service binds loopback and checks Host/Origin. It is not intended for public hosting. Browser E2E tests are provided in `tests/e2e/studio.mjs`; they require a real running local API and Playwright.

## Judge demo and screenshot

`docker compose up --build` builds and starts the CPU image at
http://localhost:8000 with persistent local results. The image has no GPU runtime
requirement. Docker execution is pending on a machine with Docker installed.
The service supports `--host 0.0.0.0` inside the container; Compose limits published
access to localhost. Host/origin checks still reject remote domains.

**Try a real demo** uses seeded synthetic 1.2 kb DNA, including substitutions and
explicit insertion/deletion events. After real alignment and three measured CPU
benchmark configurations complete, the UI opens the variant canvas and charts.
All measurements are stored with their demo job identifier.

To capture the actual UI (after installing browser prerequisites), start Studio
and run:

```sh
WARPALIGN_SCREENSHOT_DIR=docs/assets node tests/e2e/studio.mjs
```

This creates `docs/assets/studio-demo.png`. Uncomment its image in the README
after verifying the screenshot. The placeholder is intentionally not rendered
until a real screenshot exists.
