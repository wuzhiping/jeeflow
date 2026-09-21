docker-compose down
git status .
git pull origin dev
docker-compose build
docker-compose up -d
docker-compose logs -f
