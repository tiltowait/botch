FROM python:3.12-slim AS builder

ENV PIP_ROOT_USER_ACTION=ignore

WORKDIR /app

COPY pyproject.toml poetry.lock ./

# Install in project so we only copy necessary dependencies in the final stage.
# The final image won't have pip nor poetry.
RUN pip install poetry \
    && poetry config virtualenvs.in-project true \
    && poetry install --no-root --without dev

# Final stage
FROM ubuntu/python:3.12-24.04

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

# Copy only the virtual environment
COPY --from=builder /app/.venv/lib/python3.12/site-packages /usr/local/lib/python3.12/dist-packages

ENTRYPOINT ["python3", "main.py"]
