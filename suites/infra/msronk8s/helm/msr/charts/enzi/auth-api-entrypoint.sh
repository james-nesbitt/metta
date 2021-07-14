#!/bin/sh
set -o errexit

echo database host: ${DBHOST?}
echo database port: ${DBPORT?}
echo TLS directory: ${TLSDIR?}

enzicmd() {
    enzi \
        --db-addr="${DBHOST}:${DBPORT}" \
        --tls-dir="${TLSDIR}" \
        "$@"
}

while ! nc -z "${DBHOST}" "${DBPORT}"; do
    echo "Waiting for database service to be ready..."
    sleep 2
done

# Try to initialize (create) the database. If it fails, that probably
# just means the database already exists.
if enzicmd migrate-db --initial; then
    # Note:  We're setting some default, hardcoded credentials here, but
    # it is expected that this script will go away in the final product
    # and that this setup will be handled by the user through other means.
    ( export USERNAME=admin PASSWORD=password; enzicmd create-admin )
fi

enzicmd --debug api-server \
    --root-prefix=enzi \
    --login-page-location=/login/
