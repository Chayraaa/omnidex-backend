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