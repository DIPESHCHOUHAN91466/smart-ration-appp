#!/bin/sh
# MYSQL_SSL_CA=<PEM text of the database provider's CA certificate> is written to /tmp/mysql-ca.pem, which
# DATABASE_URL then references (?ssl_ca=/tmp/mysql-ca.pem) - cloud MySQL services require TLS.
# Hosting platforms pass the port in $PORT (8080 otherwise).
set -e
if [ -n "$MYSQL_SSL_CA" ]; then
  printf '%s\n' "$MYSQL_SSL_CA" > /tmp/mysql-ca.pem
fi
export ASPNETCORE_URLS="http://0.0.0.0:${PORT:-8080}"
exec dotnet SmartRation.Api.dll
