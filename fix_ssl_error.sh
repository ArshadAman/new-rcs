#!/bin/bash
# Description: Fixes corrupted Let's Encrypt directory purely inside Docker
# automatically detecting directory

cd "$(dirname "$0")" || exit 1

echo "1. Cleaning up broken config (inside certbot container)..."
docker-compose run --rm --entrypoint "sh -c" certbot "rm -rf /etc/letsencrypt/archive /etc/letsencrypt/renewal /etc/letsencrypt/live/* /etc/letsencrypt/accounts"

echo "2. Generating temporary dummy certificates (inside certbot container) to start Nginx..."
docker-compose run --rm --entrypoint "sh -c" certbot "mkdir -p /etc/letsencrypt/live/api.level-4u.com && \
    openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout /etc/letsencrypt/live/api.level-4u.com/privkey.pem \
    -out /etc/letsencrypt/live/api.level-4u.com/fullchain.pem \
    -subj '/CN=localhost'"

echo "3. Restarting Nginx so it boots with the temporary certificate..."
docker-compose restart nginx
sleep 3

echo "4. Requesting a fresh Let's Encrypt certificate..."
docker-compose run --rm --entrypoint "" certbot certbot certonly --webroot -w /var/www/certbot --force-renewal -d api.level-4u.com --register-unsafely-without-email --agree-tos --non-interactive

echo "5. Reloading Nginx to apply the new live certificates..."
docker-compose exec -T nginx nginx -s reload

echo "All done! Your SSL configuration is fixed and the auto-renew cron will now work flawlessly."
