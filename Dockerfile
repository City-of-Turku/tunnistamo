# =========================================================
FROM python:3.12-slim-bookworm AS staticbuilder
# ---------------------------------------------------------
# Stage for building static files for the project.
# Installs Node as that is required for compiling SCSS files.
# =========================================================

RUN apt-get update && apt-get install -y --no-install-recommends \
      libxmlsec1-dev \
      libxml2-dev \
      libxslt-dev \
      zlib1g-dev \
      pkg-config \
      git \
      curl \
      libpq-dev \
      build-essential \
      nodejs \
      npm \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY requirements-prod.txt /app/requirements-prod.txt
COPY requirements-prod-turku.txt /app/requirements-prod-turku.txt
COPY package.json /app/package.json

RUN pip install -U pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt
RUN npm install

COPY . /app/
RUN CACHE_URL=locmemcache://tunnistamo \
    SOCIAL_AUTH_AXIELL_AURORA_API_URL=none \
    SOCIAL_AUTH_AXIELL_AURORA_API_USERNAME=none \
    SOCIAL_AUTH_AXIELL_AURORA_API_PASSWORD=none \
    SOCIAL_AUTH_TURKU_SUOMIFI_API_URL=none \
    SOCIAL_AUTH_TURKU_SUOMIFI_API_KEY=none \
    SOCIAL_AUTH_TURKU_ADFS_SP_ENTITY_ID=none \
    SOCIAL_AUTH_OPAS_ADFS_SP_ENTITY_ID=none \
    KOHA_OAUTH_CLIENT_ID=none \
    KOHA_OAUTH_CLIENT_API_KEY=none \
    SOCIAL_AUTH_FOLI_API_ID=none \
    SOCIAL_AUTH_FOLI_API_KEY=none \
    SKIP_CERTIFICATES=true \
    python manage.py collectstatic --noinput

# ===========================================
FROM python:3.12-slim-bookworm AS appbase
# ===========================================

RUN apt-get update && apt-get install -y --no-install-recommends \
      build-essential \
      libpq-dev \
      gettext \
      git \
      libxmlsec1-dev \
      libxml2-dev \
      libxslt-dev \
      zlib1g-dev \
      netcat-openbsd \
      nodejs \
      npm \
      pkg-config \
      gdal-bin \
      dialog \
      openssh-server \
      python3-dev \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m appuser

WORKDIR /app

COPY --chown=appuser:appuser requirements.txt /app/requirements.txt
COPY --chown=appuser:appuser requirements-prod.txt /app/requirements-prod.txt
COPY --chown=appuser:appuser requirements-prod-turku.txt /app/requirements-prod-turku.txt

RUN pip install -U pip setuptools wheel \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && UWSGI_PROFILE_OVERRIDE="ssl=false" pip install --no-cache-dir -r /app/requirements-prod.txt \
    && pip install --no-cache-dir -r /app/requirements-prod-turku.txt \
    && echo "root:Docker!" | chpasswd \
    && ln -s /var/tunnistamo/node_modules /node_modules

ENV PATH="/var/tunnistamo/node_modules/.bin:${PATH}"

COPY docker-entrypoint.sh /app
RUN chmod a+x /app/docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]

COPY --from=staticbuilder --chown=appuser:appuser /app/static /fileshare/staticroot
COPY --from=staticbuilder --chown=appuser:appuser /app/node_modules /var/tunnistamo/node_modules

# ==========================
FROM appbase AS production
# ==========================

COPY --chown=appuser:appuser . /app/

COPY sshd_config /etc/ssh/
RUN chmod a+x /app/docker-entrypoint.sh \
    && echo "root:Docker!" | chpasswd

RUN chmod a+x /app/docker-entrypoint.sh

RUN echo "root:Docker!" | chpasswd

EXPOSE 8000/tcp 2222
