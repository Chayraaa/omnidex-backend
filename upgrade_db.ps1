$env:FLASK_APP = "run.py"
$env:SKIP_SERVICES = "1"
if (-not $env:JWT_SECRET) {
    $env:JWT_SECRET = "temp_secret_for_migrations"
}
if (-not $env:SQLALCHEMY_DATABASE_URI) {
    # Default to localhost if not set, as per user's port forwarding comment
    $env:SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres@localhost:5432/omnidex"
}
flask db upgrade
