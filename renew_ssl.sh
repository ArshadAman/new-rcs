#!/bin/bash
# Description: Automates SSL certificate renewal and reloads Nginx.
# Created via cron schedule.

cd /home/arshad-aman/Desktop/new-rcs || exit 1

# Run certbot to renew certificates
echo "[$(date)] Running certbot renewal..."
docker-compose run --rm certbot renew --webroot -w /var/www/certbot --quiet

# Reload NGINX to apply the new certificates without downtime
echo "[$(date)] Reloading Nginx configuration..."
docker-compose exec -T nginx nginx -s reload

echo "[$(date)] SSL renewal check complete."
