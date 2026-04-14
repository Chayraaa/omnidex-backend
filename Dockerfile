FROM python:3.12-alpine
LABEL authors="Karla Schramm"

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apk add --no-cache gcc musl-dev libffi-dev postgresql-dev bash

WORKDIR /omnidex-backend

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

COPY . .
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "run:app"]