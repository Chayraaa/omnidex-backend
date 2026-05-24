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

## Collection Service Quickstart (Docker)

This section shows how to test collection endpoints for the authenticated user:

- `GET /api/collections/me`
- `GET /api/collections/me/{entryId}`

It includes list/search/sort/category-filter behavior.

### 1) Start backend

```bash
docker compose up -d --build backend
```

### 2) Create or reuse test user

```bash
curl -s -X POST http://127.0.0.1:5000/api/users/create \
  -H "Content-Type: application/json" \
  -d '{"name":"coltest","email":"coltest@example.com","password":"Test1234!"}'
```

If user already exists, continue.

### 3) Login and export token

```bash
TOKEN=$(curl -s -X POST http://127.0.0.1:5000/api/users/login \
  -H "Content-Type: application/json" \
  -d '{"email":"coltest@example.com","password":"Test1234!"}' \
  | jq -r '.token')
echo ${#TOKEN}
```

### 4) Ensure `cards` table has collection fields (for older local DBs)

Run once if your local DB was created before the latest schema changes:

```bash
docker compose exec db psql -U postgres -d omnidex -c "
ALTER TABLE cards ADD COLUMN IF NOT EXISTS category VARCHAR;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS confidence DOUBLE PRECISION;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS description TEXT;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS source_title VARCHAR;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS source_url VARCHAR;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS alternatives_json TEXT;
ALTER TABLE cards ADD COLUMN IF NOT EXISTS created_at TIMESTAMP DEFAULT NOW();
UPDATE cards SET created_at = NOW() WHERE created_at IS NULL;
"
```

### 5) Insert sample cards for the logged-in user

Find your user id:

```bash
docker compose exec db psql -U postgres -d omnidex -c "select id,email from users order by id;"
```

Replace `<USER_ID>` below with that id (for `coltest@example.com`).

```bash
docker compose exec db psql -U postgres -d omnidex -c "
insert into cards
(name, card_summary, category, confidence, description, source_title, source_url, alternatives_json, image_key, created_at, user_id)
values
('rose', 'Rose short summary', 'Pflanze', 0.93, 'Rose description', 'Rose', 'https://en.wikipedia.org/wiki/Rose', '[]', 'http://127.0.0.1:5000/api/image/cards/<USER_ID>/rose.jpeg', now() - interval '3 day', <USER_ID>),
('cat', 'Cat short summary', 'Tiere', 0.97, 'Cat description', 'Cat', 'https://en.wikipedia.org/wiki/Cat', '[{\"label\":\"lynx\",\"confidence\":0.31}]', 'http://127.0.0.1:5000/api/image/cards/<USER_ID>/cat.jpeg', now() - interval '2 day', <USER_ID>),
('pizza', 'Pizza short summary', 'Nahrung', 0.95, 'Pizza description', 'Pizza', 'https://en.wikipedia.org/wiki/Pizza', '[]', 'http://127.0.0.1:5000/api/image/cards/<USER_ID>/pizza.jpeg', now() - interval '1 day', <USER_ID>);
"
```

### 6) Test list/search/sort/filter

Newest:

```bash
curl -s "http://127.0.0.1:5000/api/collections/me?sort=newest" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Oldest:

```bash
curl -s "http://127.0.0.1:5000/api/collections/me?sort=oldest" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Search:

```bash
curl -s "http://127.0.0.1:5000/api/collections/me?query=cat" \
  -H "Authorization: Bearer $TOKEN" | jq
```

Category filter (uses stored category only, no mapping logic):

```bash
curl -s "http://127.0.0.1:5000/api/collections/me?category=Pflanze" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 7) Test detail endpoint

```bash
ENTRY_ID=$(curl -s "http://127.0.0.1:5000/api/collections/me?sort=newest" \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['items'][0]['id'])")

curl -s "http://127.0.0.1:5000/api/collections/me/$ENTRY_ID" \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 8) Negative checks (expected `400`)

```bash
curl -s -i "http://127.0.0.1:5000/api/collections/me?sort=abc" \
  -H "Authorization: Bearer $TOKEN"

curl -s -i "http://127.0.0.1:5000/api/collections/me?category=ANIMAL" \
  -H "Authorization: Bearer $TOKEN"
```
