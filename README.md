
# Finotif
###REST API for monitoring stock market data. 
[![Build docker images](https://github.com/pkwarc/finotif/actions/workflows/docker-build.yml/badge.svg)](https://github.com/pkwarc/finotif/actions/workflows/docker-build.yml)
***
**NOTE** - The project is still under development
***
### Requirements

- [![Python >= 3.9.7](https://img.shields.io/badge/python-%3E%3D%203.9.7-blue)](https://www.python.org/downloads/release/python-397/)
- [![Poetry](https://img.shields.io/badge/poetry-1.1.10-blue)](https://github.com/python-poetry/poetry)
- [![Docker >= 20.10](https://img.shields.io/badge/%20docker-%3E%3D%2020.10-blue)](https://www.docker.com/)
- [![docker-compose >= 1.29.0](https://img.shields.io/badge/%20docker--compose-%3E%3D%201.29-blue)](https://docs.docker.com/compose/)

# Description
Interactive docs are available under `/api/docs` or [here](http://srv09.mikr.us:20342/api/docs/)

---

The api allows you to avoid tracking a property (e.g. price) of a security manually.
Instead, it lets you configure a notification that is sent automatically when the price of the security
changes by some defined value.
For a complete description visit the interactive [docs](http://srv09.mikr.us:20342/api/docs/).
Additionally, you can:
- add notes to tracked securities 
- list all tracked securities
---
## User authentication

The JSON body of the requests listed below is described in the [docs](http://srv09.mikr.us:20342/api/docs/). 
1. Register a user - send POST to `/api/user`.
2. Get a JWT - send POST to `/api/token/create`.
3. Use the JWT to authorize requests in the `Authorization: Bearer <JWT>` header.
---
## Configuration
**NOTE** - Run all commands from the project root

The project can be configured via .env file. Change .env.dev filename to .env.
Environment variables defined there will be passed to `docker-compose`[(docs)](https://docs.docker.com/compose/environment-variables/)

**NOTE** - Set at least:

    DJANGO_SECRET_KEY
    TARGET_ENV (development|production)

---

## Local development

With `TARGET_ENV=development` -> `docker-compose up`. Access in browser -> `localhost:8080`
This loads [docker-compose.override.yml](docker-compose.override.yml) and mounts app directory to container.
Any code changes will restart server dynamically.

The api health check available at `/api/ht/`

### Commands:
- Run development server - `docker-compose up`
- To run local dir tests - `docker-compose run app test`
- Access to manage.py - `docker-compose run manage {args}`
---

## Production

With `TARGET_ENV=production` -> `docker-compose -f docker-compose.yml up`. Access in browser -> `localhost:8000/api/docs/`

You can avoid building images by downloading already built images from dockerhub via
`docker-compose pull` before executing `docker-compose up`.

The api health check available at `/api/ht/`

### Commands:
- Run server - `docker-compose -f docker-compose.yml up`
- To run tests - `docker-compose -f docker-compose.yml run app test`
---

## CI/CD - Github Actions

### Current workflow

- Build docker images
- Run containers
- Run tests
- Push the docker images to the DockerHub

