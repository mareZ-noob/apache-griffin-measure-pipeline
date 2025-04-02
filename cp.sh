docker ps
read -p "Enter container id: " container_id
docker cp $container_id:/app/griffin-service.jar ./griffin-service.jar
docker cp $container_id:/app/griffin-measure.jar ./griffin-measure.jar
