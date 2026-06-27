#!/bin/sh
set -eu

: "${HERMES_VOLUME_UID:=10001}"
: "${HERMES_VOLUME_GID:=10001}"

mkdir -p /opt/data
mkdir -p /opt/data/cache
mkdir -p /opt/data/logs
mkdir -p /opt/data/profiles
mkdir -p /opt/data/sessions

chown -R "${HERMES_VOLUME_UID}:${HERMES_VOLUME_GID}" /opt/data
chmod 750 /opt/data
find /opt/data -mindepth 1 -maxdepth 1 -type d -exec chmod 750 {} \;

echo "Initialized /opt/data for uid:gid ${HERMES_VOLUME_UID}:${HERMES_VOLUME_GID}"
