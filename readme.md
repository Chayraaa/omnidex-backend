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
IMG_B64=$(python3 -c 'import base64, pathlib, sys; print(base64.b64encode(pathlib.Path(sys.argv[1]).read_bytes()).decode())' "<ABSOLUTE_IMAGE_PATH>")
printf '{"image":"%s"}' "$IMG_B64" > /tmp/scan.json
```

This Python variant is portable across Linux and macOS.

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
USER_ID=$(docker compose exec -T db psql -U postgres -d omnidex -t -A -c "select id from users where email='coltest@example.com' limit 1;")
echo "$USER_ID"
```

```bash
docker compose exec -T db psql -U postgres -d omnidex -c "
insert into cards
(name, card_summary, category, confidence, description, source_title, source_url, alternatives_json, image_key, created_at, user_id)
values
('rose', 'Rose short summary', 'Pflanze', 0.93, 'Rose description', 'Rose', 'https://en.wikipedia.org/wiki/Rose', '[]', 'http://127.0.0.1:5000/api/image/cards/' || '$USER_ID' || '/rose.jpeg', now() - interval '3 day', '$USER_ID'),
('cat', 'Cat short summary', 'Tiere', 0.97, 'Cat description', 'Cat', 'https://en.wikipedia.org/wiki/Cat', '[{\"label\":\"lynx\",\"confidence\":0.31}]', 'http://127.0.0.1:5000/api/image/cards/' || '$USER_ID' || '/cat.jpeg', now() - interval '2 day', '$USER_ID'),
('pizza', 'Pizza short summary', 'Nahrung', 0.95, 'Pizza description', 'Pizza', 'https://en.wikipedia.org/wiki/Pizza', '[]', 'http://127.0.0.1:5000/api/image/cards/' || '$USER_ID' || '/pizza.jpeg', now() - interval '1 day', '$USER_ID');
"
```

If you prefer to avoid shell interpolation inside SQL, replace the three `'$USER_ID'` occurrences manually with the numeric id.

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

If the response is `404 Not Found`, restart the backend container with a rebuild:

```bash
docker compose up -d --build backend
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

## Prerequisites And Common Issues

Before running the quickstarts, make sure you have:

- `docker` and `docker compose`
- `python3`
- `jq`
- a free local port `5000` for the backend
- a free local port `5432` or an already running PostgreSQL container managed by this compose file
- a valid `.env` file in the repo root with the required LISA and JWT variables

Common issues:

- If a route returns `404` after code changes, rebuild the backend container with `docker compose up -d --build backend`.
- If login works but `/api/scan` returns `502`, the request reached the backend and the issue is usually in the LISA response format or in LISA credentials.
- If `/api/collections/me` shows no results, check that the inserted cards belong to the same user you logged in with.
- If you use a different shell or OS, prefer the Python base64 command shown above instead of GNU-specific `base64 -w 0`.

## Caching Smoke Tests (Docker)

This section verifies the implemented HTTP caching behavior in a running backend.

Current backend routes in this branch use the `/v1` prefix. If your deployment maps the API behind another prefix, adjust the URLs accordingly.

### 1) Start backend

```bash
cd /home/prathamp/Restful/omnidex-backend
docker compose up -d --build backend
```

### 2) Wiki public cache: `ETag` and `304`

First request:

```bash
curl -sD /tmp/wiki.headers -o /tmp/wiki.body \
  http://127.0.0.1:5000/v1/wiki/summary/cat

cat /tmp/wiki.headers
cat /tmp/wiki.body | jq
```

Expected headers:

```text
HTTP/1.1 200 OK
Cache-Control: public, max-age=86400, must-revalidate
ETag: "..."
Vary: Accept
```

Revalidate with the returned `ETag`:

```bash
ETAG=$(awk -F': ' 'tolower($1)=="etag"{gsub("\r","",$2); print $2}' /tmp/wiki.headers)

curl -i \
  -H "If-None-Match: $ETAG" \
  http://127.0.0.1:5000/v1/wiki/summary/cat
```

Expected response:

```text
HTTP/1.1 304 NOT MODIFIED
Cache-Control: public, max-age=86400, must-revalidate
ETag: "..."
```

### 3) No-store check for non-cacheable scan endpoint

This does not need a valid token. The request may fail with `401`, but the response must still be marked as not cacheable.

```bash
curl -i -X POST http://127.0.0.1:5000/v1/scan \
  -H "Content-Type: application/json" \
  -d '{}'
```

Expected header:

```text
Cache-Control: no-store
```

### 4) Collection private cache: `ETag`, `Vary: Authorization`, and `304`

Create and log in a test user:

```bash
EMAIL="cache_tester_$(date +%s)@example.com"

curl -s -X POST http://127.0.0.1:5000/v1/users/create \
  -H "Content-Type: application/json" \
  -d "{\"name\":\"Cache Tester\",\"email\":\"$EMAIL\",\"password\":\"test12345\"}" | jq

TOKEN=$(curl -s -X POST http://127.0.0.1:5000/v1/users/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$EMAIL\",\"password\":\"test12345\"}" | jq -r .access_token)

echo ${#TOKEN}
```

Call the collection endpoint:

```bash
curl -sD /tmp/collection.headers -o /tmp/collection.body \
  http://127.0.0.1:5000/v1/collections/me \
  -H "Authorization: Bearer $TOKEN"

cat /tmp/collection.headers
cat /tmp/collection.body | jq
```

Expected headers:

```text
HTTP/1.1 200 OK
Cache-Control: private, no-cache
ETag: "..."
Vary: Authorization
```

Revalidate:

```bash
COLLECTION_ETAG=$(awk -F': ' 'tolower($1)=="etag"{gsub("\r","",$2); print $2}' /tmp/collection.headers)

curl -i \
  -H "Authorization: Bearer $TOKEN" \
  -H "If-None-Match: $COLLECTION_ETAG" \
  http://127.0.0.1:5000/v1/collections/me
```

Expected response:

```text
HTTP/1.1 304 NOT MODIFIED
Cache-Control: private, no-cache
ETag: "..."
Vary: Authorization
```

### 5) Optional image cache check

Use an `image_reference` returned by a real scan response.

```bash
IMAGE_URL="<IMAGE_REFERENCE_FROM_SCAN_RESPONSE>"

curl -sD /tmp/image.headers -o /tmp/image.body "$IMAGE_URL"
cat /tmp/image.headers
```

Expected headers:

```text
HTTP/1.1 200 OK
Cache-Control: private, max-age=86400, must-revalidate
ETag: "..."
```

Revalidate:

```bash
IMAGE_ETAG=$(awk -F': ' 'tolower($1)=="etag"{gsub("\r","",$2); print $2}' /tmp/image.headers)

curl -i \
  -H "If-None-Match: $IMAGE_ETAG" \
  "$IMAGE_URL"
```

Expected response:

```text
HTTP/1.1 304 NOT MODIFIED
```

### 6) Optional `If-Match` conflict check for category update

This requires an existing collection entry id. Use any `id` from `GET /v1/collections/me`.

```bash
ENTRY_ID="<ENTRY_ID_FROM_COLLECTION_RESPONSE>"

curl -i -X PATCH "http://127.0.0.1:5000/v1/collections/me/$ENTRY_ID/category" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -H 'If-Match: "stale-etag"' \
  -d '{"category":"Pflanze"}'
```

Expected response:

```text
HTTP/1.1 412 PRECONDITION FAILED
Cache-Control: no-store
```
