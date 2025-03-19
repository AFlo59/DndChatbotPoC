docker-compose up --build

docker-compose down
docker system prune -af --volumes
sudo rm -rf data
mkdir data
sudo chown -R $USER:$USER data
docker-compose up --build


docker-compose down --volumes

docker system prune -f

sudo lsof -i :8000

docker ps

docker ps -a


mkdir -p data

docker-compose down -v
docker-compose up --build