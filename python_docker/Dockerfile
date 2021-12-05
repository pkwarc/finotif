FROM python:3.9.7-slim as python-base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"


# builder-base is used to build dependencies
FROM python-base as builder-base

RUN apt-get update \
    && apt-get install --no-install-recommends -y \
    curl \
    build-essential

# Install Poetry - respects $POETRY_VERSION & $POETRY_HOME
ARG POETRY_VERSION
RUN curl -sSL https://raw.githubusercontent.com/sdispater/poetry/master/get-poetry.py | python

# We copy our Python requirements here to cache them
# and install only tuntime deps using poetry
WORKDIR $PYSETUP_PATH
COPY ./poetry.lock ./pyproject.toml ./
RUN poetry install --no-dev


# 'development' stage install all dev deps and can be used to develop code
# For example using docker-compose to mount local volume under /app
FROM python-base as development

# Copying poetry and venv into image
COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

WORKDIR $PYSETUP_PATH
RUN poetry install

COPY . /app
WORKDIR /app
RUN ["chmod", "+x", "./python_docker/entrypoint-dev.sh"]
ENTRYPOINT ./python_docker/entrypoint-dev.sh $0 $@


FROM python-base as production
# default docker-compose healthcheck requires curl
RUN apt-get update && apt-get install -y curl

COPY --from=builder-base $VENV_PATH $VENV_PATH
COPY . /app
WORKDIR /app
RUN ["chmod", "+x", "./python_docker/entrypoint.sh"]
ENTRYPOINT ./python_docker/entrypoint.sh $0 $@
