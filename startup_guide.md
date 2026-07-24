# 1. Поднять кластер kind
kind create cluster --name umnaya

# 2. Подготовить папки для PersistentVolume
docker exec umnaya-control-plane mkdir -p /var/lib/umnaya/{postgres,minio,kafka}

# 3. Собрать образ приложения
docker build -t umnaya-api .

# 4. Загрузить образ в kind
kind load docker-image umnaya-api --name umnaya

# 5. Применить все манифесты k8s
kubectl apply -f k8s/

# 6. Дождаться готовности подов
kubectl get pods -n umnaya -w

# 7. Открыть доступ к API (в отдельном терминале)
kubectl port-forward -n umnaya svc/api-service 8000:8000 --address 0.0.0.0

пересборка после изменений:

# 1. Собрать новый образ
docker build -t umnaya-api .

# 2. Загрузить в kind
kind load docker-image umnaya-api --name umnaya

# 3. Перезапустить поды API и Worker (чтобы взяли новый образ)
kubectl delete pod -n umnaya -l app=api
kubectl delete pod -n umnaya -l app=worker

остановка:

kubectl scale deployment -n umnaya --all --replicas=0