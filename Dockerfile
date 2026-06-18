FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=laundry_advisor.settings.prod

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Build Tailwind and collect static files at image build time.
# SECRET_KEY is required by Django settings even for non-secret build steps.
ARG SECRET_KEY=build-placeholder-key
ARG DATABASE_URL=sqlite:////tmp/build.db
ARG AWS_STORAGE_BUCKET_NAME=placeholder
ARG AWS_ACCESS_KEY_ID=placeholder
ARG AWS_SECRET_ACCESS_KEY=placeholder
RUN python manage.py tailwind download_cli && \
    python manage.py tailwind build && \
    rm -rf assets/src/ && \
    python manage.py collectstatic --no-input

RUN useradd --no-create-home --system appuser && chown -R appuser /app
USER appuser

EXPOSE 8000

COPY --chown=appuser entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
