# WarpAlign Studio

Build the frontend and start the loopback API:

```sh
cd apps/studio && npm install && npm run build
cd ../..
warpalign-studio
```

Open http://127.0.0.1:8000. Development alternative: start `npm run dev` in `apps/studio` alongside the API. Vite proxies `/api` locally.

Dashboard shows actual service status and session runs. New alignment uploads local input files. Results shows progress and paginates 200 rows, with search and sorting within that page. Download exports the completed run, including sequences. Viewer paints only the visible CIGAR-indexed columns onto canvas. Performance lab times real seeded CPU calls; unavailable GPU charts remain empty. Settings stores defaults in browser localStorage and clears completed server runs.

The service rejects non-local Host/Origin values, bounds uploads and queued jobs, binds 127.0.0.1, and deletes temporary uploads after each job. No sequence telemetry or cloud upload is implemented. Session results are in memory, not durable storage. Use the CLI for large jobs; do not expose this unauthenticated local service on a public interface.
