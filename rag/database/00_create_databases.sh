#!/bin/bash
# Crea la BD 'admin' para que clientes sin BD explícita no fallen
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "postgres" <<-EOSQL
    SELECT 'CREATE DATABASE admin' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'admin')\gexec
EOSQL
