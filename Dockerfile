FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml requirements.txt ./
RUN pip install --no-cache-dir .

COPY . .

ENV CONFIG_FILE=/app/config.yaml
ENV DAEMON=true
ENV RUN_INTERVAL=600

CMD ["vinted-notifier", "--config", "/app/config.yaml", "--daemon"]
