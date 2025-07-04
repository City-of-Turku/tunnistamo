# =========================================================
FROM helsinkitest/python-node:3.6-12-slim as staticbuilder
# ---------------------------------------------------------
# Stage for building static files for
# the project. Installs Node as that
# is required for compiling SCSS files.
# =========================================================

RUN apt-install.sh \
      libxmlsec1-dev \
      libxml2-dev \
      pkg-config \
      git \
      curl \
      libpq-dev \
      build-essential

WORKDIR /app

COPY requirements.txt /app/requirements.txt
COPY requirements-prod.txt /app/requirements-prod.txt
COPY requirements-prod-turku.txt /app/requirements-prod-turku.txt
COPY package.json /app/package.json
RUN pip install -U pip \
    && pip install --no-cache-dir  -r /app/requirements.txt \
    && pip install --no-cache-dir  -r /app/requirements-prod.txt \
    && pip install --no-cache-dir  -r /app/requirements-prod-turku.txt
RUN npm install

COPY . /app/
RUN CACHE_URL=pymemcache:// SOCIAL_AUTH_AXIELL_AURORA_API_URL=none SOCIAL_AUTH_AXIELL_AURORA_API_USERNAME=none SOCIAL_AUTH_AXIELL_AURORA_API_PASSWORD=none SOCIAL_AUTH_TURKU_SUOMIFI_API_URL=none SOCIAL_AUTH_TURKU_SUOMIFI_API_KEY=none SOCIAL_AUTH_TURKU_ADFS_SP_ENTITY_ID=none SOCIAL_AUTH_OPAS_ADFS_SP_ENTITY_ID=none KOHA_OAUTH_CLIENT_ID=none KOHA_OAUTH_CLIENT_API_KEY=none SOCIAL_AUTH_FOLI_API_ID=none SOCIAL_AUTH_FOLI_API_KEY=none SKIP_CERTIFICATES=true python manage.py collectstatic --noinput

# ===========================================
FROM helsinkitest/python:3.6-slim as appbase
# ===========================================

WORKDIR /app

COPY --chown=appuser:appuser requirements.txt /app/requirements.txt
COPY --chown=appuser:appuser requirements-prod.txt /app/requirements-prod.txt
COPY --chown=appuser:appuser requirements-prod-turku.txt /app/requirements-prod-turku.txt

# Install main project dependencies and clean up
# Note that production dependencies are installed here as well since
# that is the default state of the image and development stages are
# just extras.
RUN apt-install.sh \
      build-essential \
      libpq-dev \
      gettext \
      git \
      libxmlsec1-dev \
      libxml2-dev \
      netcat \
      nodejs \
      pkg-config \
      gdal-bin \
      dialog \
      openssh-server \
    && pip install -U pip \
    && pip install --no-cache-dir  -r /app/requirements.txt \
    && pip install --no-cache-dir  -r /app/requirements-prod.txt \
    && pip install --no-cache-dir  -r /app/requirements-prod-turku.txt \
    && echo "root:Docker!" | chpasswd \
    && apt-cleanup.sh build-essential pkg-config git \
    # This application uses node-sass to compile SCSS files in runtime, and the node-sass-tilde-importer to transform @import "~" to node_modules path; this only works if SCSS files have an ancestor directory that contains node_modules; since we have static files, including SCSS files, in /fileshare out of convention, let's create a node_modules symlink to / so the importer works
    && ln -s /var/tunnistamo/node_modules /node_modules

COPY docker-entrypoint.sh /app
RUN chmod a+x /app/docker-entrypoint.sh

ENTRYPOINT ["./docker-entrypoint.sh"]

COPY --from=staticbuilder --chown=appuser:appuser /app/static /fileshare/staticroot
COPY --from=staticbuilder --chown=appuser:appuser /app/node_modules /var/tunnistamo/node_modules

# ==========================
FROM appbase as production
# ==========================

COPY --chown=appuser:appuser . /app/

# Enable SSH
COPY sshd_config /etc/ssh/

RUN chmod a+x /app/docker-entrypoint.sh

RUN echo "root:Docker!" | chpasswd

EXPOSE 8000/tcp 2222
