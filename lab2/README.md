# Лабораторная работа №2

Развёртывание Kubernetes + Helm (Minikube)

## Цель работы

- Развернуть локальный Kubernetes кластер с помощью Minikube
- Запустить сервис в Kubernetes используя YAML-манифесты (Deployment, Service, ConfigMap)
- Проверить доступность сервиса
- Создать Helm Chart на основе развернутого сервиса
- Выполнить upgrade релиза через Helm
- Разобраться с возникшими проблемами при развертывании

# Кубер справка

Kubernetes — это система оркестрации контейнеров, которая автоматически запускает, масштабирует и управляет приложениями в контейнерах

Deployment — автоматизация подов

Service — доступ к подам

Helm - менеджер для куба

## Установка Minikube и kubectl и запуск

```
sudo apt update
sudo apt install -y curl apt-transport-https

curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube

curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
chmod +x kubectl
sudo mv kubectl /usr/local/bin/
```

Проверка:
```
kubectl version --client
minikube version
```

![telegram-cloud-photo-size-2-5402325133701092481-y](https://github.com/user-attachments/assets/9af41303-6c58-4c84-a203-db9cacca8057)

При запуске `minikube start` я столкнулся с ошибкой что от рута не едет, запустил от своего пользака добавил в docker группу:
```
sudo usermod -aG docker $USER
newgrp docker
```

![telegram-cloud-photo-size-2-5402325133701092485-y](https://github.com/user-attachments/assets/d52d83f7-5b2e-40b4-9e8f-959ef32eb11d)

Проверка:
```
andrey@m5:~$ kubectl get nodes
NAME       STATUS   ROLES           AGE   VERSION
minikube   Ready    control-plane   21s   v1.35.1
```

# Часть 1. Kubernetes - YAML деплой

## Создание манифестов

1. ConfigMap
```
apiVersion: v1
kind: ConfigMap
metadata:
  name: hello-config
data:
  MESSAGE: "Hello from Kubernetes!"
```

2. Deployment
```
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hello-deployment
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hello
  template:
    metadata:
      labels:
        app: hello
    spec:
      containers:
      - name: hello-container
        image: nginxdemos/hello
        ports:
        - containerPort: 80
```
3. Service (NodePort)
```
apiVersion: v1
kind: Service
metadata:
  name: hello-service
spec:
  type: NodePort
  selector:
    app: hello
  ports:
    - port: 80
      targetPort: 80
      nodePort: 30007
```
После деплой в кластер:
```
andrey@m5:~/devops/lab2$ kubectl apply -f .
configmap/hello-config created
deployment.apps/hello-deployment created
service/hello-service created
```

Проверяем что все поднялось:

![telegram-cloud-photo-size-2-5402325133701092493-y](https://github.com/user-attachments/assets/70c418cb-629c-4461-b875-1b5b443f0be7)

## Проверка доступности

`minikube service hello-service --url`
выдает нам ip:port где запущен -  http://192.168.49.2:30007

Чтобы открыть локально на ноуте можно сделать порт форвардинг:
```
kubectl port-forward service/hello-service 8080:80
```
```
andrey@m5:~/devops/lab2$ kubectl port-forward service/hello-service 8080:80
Forwarding from 127.0.0.1:8080 -> 80
Forwarding from [::1]:8080 -> 80
```

Доступ к сервеку по ssh так что в соседнем терминале - `ssh -L 8080:localhost:8080 andrey@ip`

Получаем таккую схему:

Браузер > Kubernetes Service (NodePort) > Под > Контейнер > nginxdemos/hello (наш nginx)

Также проверим курлом:
```
andrey@m5:~/devops/lab2curl http://192.168.49.2:30007
<!DOCTYPE html>
<html>
<head>
<title>Hello World</title>
<link href="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAYAAACqaXHeAAAGPElEQVR42u1bDUyUdRj/iwpolMlcbZqtXFnNsuSCez/OIMg1V7SFONuaU8P1MWy1lcPUyhK
```

В первой части лабы был успешно развернут локальный Kubernetes-кластер с использованием Minikube, в котором через YAML-манифесты были созданы и запущены основные ресурсы (Deployment, Service и ConfigMap). В результате было задеплоено тестовое приложение “Hello World”

# Часть 2 - Helm

Устанавливаем helm:
```
root@m5:/home/andrey/devops/lab2# curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
```

Проверка:
```
root@m5:/home/andrey/devops/lab2# helm version
version.BuildInfo{Version:"v3.20.2", GitCommit:"8fb76d6ab555577e98e23b7500009537a471feee", GitTreeState:"clean", GoVersion:"go1.25.9"}
```

Создаем helm chart:
```
root@m5:/home/andrey/devops/lab2# helm create hello-chart
Creating hello-chart
```

Устанавливаем helm релиз:
```
helm install hello-release ./hello-chart
```
![telegram-cloud-photo-size-2-5402325133701092509-y](https://github.com/user-attachments/assets/33b501c2-df9c-40f1-bcc1-a9e697d8e8c0)


![telegram-cloud-photo-size-2-5402325133701092511-y](https://github.com/user-attachments/assets/6775c9df-419f-4b6b-9d50-ed8e0fea7ccb)


Проверяем что запущен:

```
andrey@m5:~/devops/lab2$ kubectl get pods
NAME                                         READY   STATUS    RESTARTS   AGE
hello-deployment-5fc85547d7-l48qq            1/1     Running   0          14m
hello-deployment-5fc85547d7-w8hrv            1/1     Running   0          14m
hello-release-hello-chart-855c9cd69c-lfllr   1/1     Running   0          31s
andrey@m5:~/devops/lab2$
```

Теперь попробуем внести изменения - поменяем версию nginx в values.yaml на `0.3`:

![telegram-cloud-photo-size-2-5402325133701092514-y](https://github.com/user-attachments/assets/a5f34c63-0664-4841-bc7e-479efc69ee31)

Сохраняем и апгрейдим:
```
helm upgrade hello-release ./hello-chart
```

Проверяем историю - `helm history hello-release'

<img width="1766" height="156" alt="telegram-cloud-document-2-5402325133241130423" src="https://github.com/user-attachments/assets/bb842db2-7526-40f9-9807-7165f3e9c34f" />

Далее столкнулся с проблемой:

```
andrey@m5:~$ channel 2: open failed: connect failed: Connection refused
channel 2: open failed: connect failed: Connection refused
```

Идем смотреть что не так - видим `ImagePullBackOff`:

![telegram-cloud-photo-size-2-5402325133701092522-y](https://github.com/user-attachments/assets/9f8061b6-3753-44a5-af3e-b45439e2c514)

Занимаемся отладкой - `kubectl describe pod hello-release-hello-chart-6f56fc4ff4-brrsm`

![telegram-cloud-photo-size-2-5402325133701092523-y](https://github.com/user-attachments/assets/d3ca6a09-792c-4182-a34a-58c8bb1470c6)

Не тянется образ тк неверный тэг - лезем на dockerhub

Там ищем один из последних образов - берем `1.29-alpine`

![telegram-cloud-photo-size-2-5402325133701092524-y](https://github.com/user-attachments/assets/529cf989-cd6e-4637-b286-64309f76aade)

Еще раз апгрейдим и смотрим что все поднялось:
```
andrey@m5:~/devops/lab2$ helm upgrade hello-release ./hello-chart
Release "hello-release" has been upgraded. Happy Helming!


andrey@m5:~/devops/lab2$ kubectl get pods
NAME                                         READY   STATUS    RESTARTS   AGE
hello-deployment-5fc85547d7-l48qq            1/1     Running   0          24m
hello-deployment-5fc85547d7-w8hrv            1/1     Running   0          24m
hello-release-hello-chart-66f55f5767-9ffg6   1/1     Running   0          16s
```

также еще раз глянем в историю:
```
andrey@m5:~/devops/lab2$ helm history hello-release
REVISION UPDATED                  STATUS     CHART             APP VERSION DESCRIPTION     
1        Tue Apr 14 14:53:03 2026 superseded hello-chart-0.1.0 1.16.0      Install complete
2        Tue Apr 14 14:55:02 2026 superseded hello-chart-0.1.0 1.16.0      Upgrade complete
3        Tue Apr 14 15:03:28 2026 deployed   hello-chart-0.1.0 1.16.0      Upgrade complete
```

Прокидываем порт `ssh -L 8081:localhost:8081 andrey@ip` и смотрим что вышло:

![telegram-cloud-photo-size-2-5402325133701092538-y](https://github.com/user-attachments/assets/dd369494-2f56-42ec-8f67-41487019c94a)

Ура-ура все работает!

# ВАЖНАЯ ЗАМЕЧАНИЕ

Только при написании отчета я заметил строчку в задании - `(сервис любой из своих не опенсорсных, вывод “hello world” в браузер тоже подойдёт)`

Поэтому... Быстренько клипаем Hello wolrd python приложуху XD

Наш супер мега сложный app.py:

<img width="371" height="198" alt="image" src="https://github.com/user-attachments/assets/2464f1ac-63fa-4cfc-9a53-73b87d36226c" />

Не менее умопомрачительный Dockerfile:

<img width="334" height="207" alt="image" src="https://github.com/user-attachments/assets/1a50365b-1cda-4132-aabc-4c3c847cc470" />

Окружение - `eval $(minikube docker-env)` 

Билдим образ - `docker build -t my-flask-app:1.0 .`

Переписываем Deployment и Service: 

<img width="440" height="390" alt="image" src="https://github.com/user-attachments/assets/2fbe1448-5d03-4697-91b5-745731ab888c" />

<img width="354" height="280" alt="image" src="https://github.com/user-attachments/assets/3f39ad3f-3264-40a7-9e07-f4b28c6b1669" />

Применяем манифесты:

```
kubectl apply -f deployment.yaml
kubectl apply -f service.yaml
```

Проверка:

<img width="599" height="118" alt="image" src="https://github.com/user-attachments/assets/ae11208a-0383-493b-a049-dc64d0d42580" />

Теперь все по заданию!

# Три причины, по которым использовать хелм удобнее чем классический деплой через кубернетес манифесты

1. Шаблонизация
   
   В Helm используются шаблоны, поэтому один и тот же chart можно использовать для разных окружений. В обычных k8s манифестах ты бы сам везде меняешь енвы образы и тд. В Helm все через values.yaml
2. Управление версиями
   
   Вся история в `helm history hello-release`. Можно роллбэкнуться например `helm rollback hello-release 1`
3. Удобное обновление
   
   `helm upgrade hello-release ./chart` и он сам обновляет Deployment, Service, пересоздаёт поды и применяет изменения аккуратно

# Итоги

В ходе лабораторной работы было:

- развернут Minikube кластер
- создан сервис через YAML (Deployment + Service + ConfigMap)
- проверена работа через NodePort и port-forward
- создан Helm Chart
- выполнен Helm upgrade
- устранены ошибки (root, image pull, port-forward)
