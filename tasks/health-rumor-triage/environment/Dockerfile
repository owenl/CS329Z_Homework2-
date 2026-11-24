# Environment for the health-rumor-triage task.
FROM python:3.12.16-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337

WORKDIR /app
COPY claims.csv /app/claims.csv
COPY RULES.md /app/RULES.md
COPY evidence/ /app/evidence/
