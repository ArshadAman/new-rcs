#!/bin/sh
# Reload nginx after certificate renewal
docker-compose -f /app/docker-compose.yml exec -T nginx nginx -s reload || true


