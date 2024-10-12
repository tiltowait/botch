FROM python:3.12-slim

# Set ENV in Railway, not here!

WORKDIR /app

COPY . .

RUN pip install poetry \
	&& poetry config virtualenvs.create false \
	&& poetry install --no-root --without dev

CMD ["python", "main.py"]
