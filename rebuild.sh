echo "Pulling latest changes..."
git pull origin master
echo "Rebuilding project..."
docker-compose down
docker-compose up -d --build
docker-compose exec web python manage.py migrate
echo "Project rebuilt successfully."