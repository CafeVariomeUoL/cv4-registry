FROM python:3.11-slim

LABEL org.opencontainers.image.title="Decentralised Discovery Network Registry"
LABEL org.opencontainers.image.description="A network registry for Decentralised Discovery Gateway systems to report the networks for public finding."
LABEL org.opencontainers.image.authors="wangyunze16@gmail.com"
LABEL org.opencontainers.image.url="https://github.com/Firefox2100/dedi-registry"
LABEL org.opencontainers.image.source="https://github.com/Firefox2100/dedi-registry"
LABEL org.opencontainers.image.vendor="uk.co.firefox2100"
LABEL org.opencontainers.image.licenses="GPL-3.0"

ENV PYTHONUNBUFFERED=1
ENV DR_ENV_FILE="/app/conf/.env"

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash ca-certificates curl && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd --system appgroup && \
    useradd --system --no-create-home --gid appgroup appuser

WORKDIR /app
COPY ./src/dedi_registry /app/src/dedi_registry
COPY ./conf /app/conf
COPY ./pyproject.toml /app/pyproject.toml
COPY ./example.env /app/conf/.env
COPY ./LICENSE /app/LICENSE
COPY ./README.md /app/README.md

RUN pip install --upgrade pip && \
    pip install . && \
    chown -R appuser:appgroup /app

USER appuser

EXPOSE 5000

HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl --fail http://localhost:5000/health || exit 1

VOLUME ["/app/conf"]

ENTRYPOINT ["uvicorn", "dedi_registry.asgi:application"]
CMD ["--host", "0.0.0.0", "--port", "5000", "--log-config", "/app/conf/uvicorn-log.config.yaml"]
