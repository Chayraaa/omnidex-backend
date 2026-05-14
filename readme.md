# Omnidex Backend API
This repository contains the backend API for Omnidex.
The Omnidex is an app that allows users to capture images and keep them
as cards in a collection. The images will be classified into a name and other
attributes like type etc.

Based on the name, the wikipedia API will be used to get a description of the
primary item in the image. The combination of image, description and the other attributes
will be used to create the finished card.

# Features
- Collection of objects as cards
- Activity feed between friends
- Global activity feed for newly discovered objects
- more to come...

## Architecture
- Based on Hexagonal Architecture
- Logic partitioned in services

## External APIs
- Wikipedia API
- LISA

## Used Technologies
### Server
- Flask
- SQLAlchemy
- PostgreSQL
### Security
- PyJWT
- Passlib
- Bcrypt
### Deployment
- Docker
- Docker Compose
- Gunicorn
### Documentation and Verification
- OpenAPI
- Swagger UI

## AI Usage
See [AI Usage](ai-usage-protocol.md)

(Note: The first 11 commits had to be rebased due to the wrong email address. Were done between 4.4.2026 and 14.4.2026)

## Scan Endpoint Quickstart (Docker)

This section shows how to run the backend and call `POST /api/scan` end-to-end (LISA recognition + Wikipedia enrichment + summary + DB persistence).

### 1) Configure environment

Create `.env` in the repo root (same folder as `docker-compose.yaml`):

```bash
cat > .env <<'EOF'
JWT_SECRET=<CHANGE_ME_JWT_SECRET>
LISA_BASE_URL=https://chat-1.ki-awz.iisys.de
LISA_API_KEY=<PASTE_REAL_LISA_TOKEN_HERE>
LISA_MODEL=lisa-vision
LISA_SUMMARY_MODEL=lisa-vision
LISA_TIMEOUT_SECONDS=60
LISA_SUMMARY_TIMEOUT_SECONDS=60
GUNICORN_CMD_ARGS=--timeout 180
EOF
```

What you must replace:
- `<CHANGE_ME_JWT_SECRET>`
- `<PASTE_REAL_LISA_TOKEN_HERE>`

### 2) Start services

```bash
docker compose up -d --build --force-recreate
docker compose logs -f backend
```

Wait until backend logs show workers booted and DB tables available.

### 3) Create a test user

```bash
curl -s -X POST http://127.0.0.1:5000/api/users/create \
  -H "Content-Type: application/json" \
  -d '{"name":"scan_tester","email":"scan_tester@example.com","password":"Test1234!"}'
```

If user already exists, continue.

### 4) Login and store JWT

Using `jq`:

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"scan_tester@example.com","password":"Test1234!"}' | jq -r '.token')
```

Quick check:

```bash
echo ${#TOKEN}
```

### 5) Build scan payload from local image

Replace `<ABSOLUTE_IMAGE_PATH>` with your file path:

```bash
IMG_B64=$(base64 -w 0 "<ABSOLUTE_IMAGE_PATH>")
printf '{"image":"%s"}' "$IMG_B64" > /tmp/scan.json
```

### 6) Call scan endpoint

```bash
curl -s -X POST http://127.0.0.1:5000/api/scan \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  --data-binary @/tmp/scan.json
```

Expected response fields include:
- `id`
- `label`
- `description`
- `card_summary`
- `summary_generated_by_ai`
- `image_reference`

### 7) Verify DB persistence

```bash
docker compose exec db psql -U postgres -d omnidex -c "select id,name,card_summary,image_key,user_id from cards order by id desc limit 5;"
```

### 8) Verify image URL works

Use the `image_reference` returned by `/api/scan`:

```bash
curl -I "<IMAGE_REFERENCE_FROM_SCAN_RESPONSE>"
```

Expected: `HTTP/1.1 200 OK` and `Content-Type` for the stored image type.
