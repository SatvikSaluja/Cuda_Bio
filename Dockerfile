# CPU demo image: no NVIDIA driver, CUDA toolkit or Python GPU dependencies.
FROM node:22-bookworm-slim AS studio
WORKDIR /src/apps/studio
COPY apps/studio/package*.json ./
RUN npm ci
COPY apps/studio/ ./
RUN npm run build && npm test

FROM python:3.12-slim-bookworm AS builder
RUN apt-get update && apt-get install -y --no-install-recommends g++ cmake && rm -rf /var/lib/apt/lists/*
WORKDIR /src
COPY . .
COPY --from=studio /src/apps/studio/dist ./apps/studio/dist
RUN cmake -S . -B /tmp/cpu-build -DENABLE_CUDA=OFF -DCMAKE_BUILD_TYPE=Release \
    && cmake --build /tmp/cpu-build -j2 \
    && ctest --test-dir /tmp/cpu-build --output-on-failure
RUN python -m pip wheel --wheel-dir /wheels '.[studio]'

FROM python:3.12-slim-bookworm AS runtime
RUN apt-get update && apt-get install -y --no-install-recommends libstdc++6 && rm -rf /var/lib/apt/lists/*
COPY --from=builder /wheels /wheels
RUN python -m pip install --no-cache-dir --no-index --find-links=/wheels 'warpalign[studio]' \
    && rm -rf /wheels \
    && useradd --create-home --uid 10001 warpalign \
    && mkdir /data && chown warpalign:warpalign /data
USER warpalign
ENV WARPALIGN_DATA_DIR=/data PYTHONUNBUFFERED=1
VOLUME ["/data"]
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/status', timeout=3)"
CMD ["warpalign-studio", "--host", "0.0.0.0", "--port", "8000"]
