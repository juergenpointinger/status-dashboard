# Status (GitLab) Dashboard

[![Docker Cloud Build Status](https://img.shields.io/docker/cloud/build/juergenpointinger/status-dashboard)](https://hub.docker.com/r/juergenpointinger/status-dashboard)
[![Docker Image Version (latest semver)](https://img.shields.io/docker/v/juergenpointinger/status-dashboard)](https://hub.docker.com/r/juergenpointinger/status-dashboard)
[![Docker Pulls](https://img.shields.io/docker/pulls/juergenpointinger/status-dashboard)](https://hub.docker.com/r/juergenpointinger/status-dashboard)
[![Docker Image Size (latest semver)](https://img.shields.io/docker/image-size/juergenpointinger/status-dashboard)](https://hub.docker.com/r/juergenpointinger/status-dashboard)
[![GitHub](https://img.shields.io/github/license/juergenpointinger/status-dashboard)](https://github.com/juergenpointinger/status-dashboard/blob/master/LICENSE)
[![Twitter Follow](https://img.shields.io/twitter/follow/pointij?style=social)](https://twitter.com/pointij)

The dashboard is intended to simplify the presentation of the evolution of products and projects for different stakeholders. 

It uses GitLab APIs and is based on Python with Plotly Dash.

Tested with:

- Python 3.10
- Dash 2.7.0
- Plotly 5.12
- GitLab 15+

## Routes

| Route               | Description      | Image                                  |
|:--------------------|:-----------------|:---------------------------------------|
| `/` or `/dashboard` | Status Dashboard | [Preview](./docs/status-dashboard.png) |
| `/monitor`          | Build Monitor    | [Preview](./docs/build-monitor.png)    |

## Environment

| Key | Description | Default |
|:-------------------|:------------|:--------|
| GITLAB_TOKEN       | GitLab token will be used whenever the API is invoked | |
| GITLAB_GROUP_ID    | GitLab group id | |
| GITLAB_PROJECT_IDS | GitLab project id list (Json format) | see `.env.example` for details |
| DEBUG              | Debug mode (optional) | false |
| LOGLEVEL           | Logging level (optional) | INFO |
| LOGFORMAT          | Logging format output (optional) | %(asctime)s - %(levelname)s - %(message)s |
| APP_NAME           | Dashboard application name (optional) | Status Dashboard |
| APP_HOST           | Dashboard host ip adress (optional) | 0.0.0.0 (for Docker environment) |
| APP_PORT           | Dashboard port (optional) | 5000 |
| REDIS_URL          | Redis url | redis://localhost:6379 |

Rename your `.env.example` to `.env` and add the required changes.

## Run locally

```bash
$ pip install -r requirements.txt
$ python3 index.py
```

## Run via Docker

```bash
$ docker run --rm --name redis -p 6379:6379 redis:7.0-alpine
$ docker run --rm --env-file .env --name status-dashboard -p 5000:5000 juergenpointinger/status-dashboard:latest
```

## Build via Docker

```bash
$ docker-compose up -d
$ docker build . -t juergenpointinger/status-dashboard:latest
$ docker run --rm --name status-dashboard -p 5000:5000 juergenpointinger/status-dashboard:latest
```