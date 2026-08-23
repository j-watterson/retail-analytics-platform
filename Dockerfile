FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY src ./src
RUN pip install --no-cache-dir .

COPY configs ./configs
COPY data ./data
COPY sql ./sql

RUN mkdir -p /app/warehouse /app/data/rejected \
    && chown -R 10001:10001 /app

USER 10001

ENTRYPOINT ["retail-etl"]
CMD ["--report"]

