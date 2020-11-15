#!/usr/bin/env bash
python ci-env-migrate/gh.py $TRAVIS_REPO_SLUG \
  "CODACY_PROJECT_TOKEN=$CODACY_PROJECT_TOKEN" \
  "DOCKER_USR=$DOCKER_USR" \
  "DOCKER_PWD=$DOCKER_PWD" \
  "PYPI_TOKEN=$TWINE_PASSWORD" \
  "SNAP_TOKEN=$SNAP_TOKEN" \
  "GPG_KEY=$(gpg --export-secret-key --armour tqdm@caspersci.uk.to)"
