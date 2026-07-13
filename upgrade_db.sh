#!/bin/bash
export FLASK_APP=run.py
export SKIP_SERVICES=1
export JWT_SECRET=${JWT_SECRET:-temp_secret_for_migrations}
export SQLALCHEMY_DATABASE_URI=${SQLALCHEMY_DATABASE_URI:-"postgresql://postgres:postgres@localhost:5432/omnidex"}
flask db upgrade
