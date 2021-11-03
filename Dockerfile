FROM python:3.9.7-slim

WORKDIR /var/www/app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PIP_DISABLE_PIP_VERSION_CHECK=on

ARG POETRY_VERSION

RUN pip install "poetry==$POETRY_VERSION"
COPY poetry.lock pyproject.toml /var/www/app/

# Project initializtion
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

COPY . /var/www/app

RUN ["chmod", "+x", "./entrypoint.sh"]

ENTRYPOINT ./entrypoint.sh $0 $@
