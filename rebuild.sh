echo "Pulling latest changes..."
git fetch origin master
git reset --hard origin/master
echo "Rebuilding project..."
docker-compose down
docker-compose up -d --build
docker-compose exec web python manage.py migrate
echo "Project rebuilt successfully."