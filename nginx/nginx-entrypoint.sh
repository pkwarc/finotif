#! /usr/bin/env sh

# exit if any command fails, throw error on unset variables
set -eu

envsubst '${APP_PORT} ${NGINX_PORT}' < /etc/nginx/conf.d/nginx.default.conf > /etc/nginx/conf.d/nginx.conf
rm /etc/nginx/conf.d/nginx.default.conf

# exec dockerfile CMD
exec "$@"
