# DevOps Lab 1 - Docker

## Задание 
Разработайте утилиту на любом удобном языке программирования (например, Go, Python), которая запускает команду в контейнере.
Должна конфигурироваться config.json по спецификации OCI
Для каждого контейнера при его запуске должны создаваться новые namespaces:

- PID namespace;
- Mount namespace;
- UTS namespace, внутри которого hostname устанавливается в значение из поля hostname конфига
  
Для каждого контейнера с идентификатором <id> должна создаваться директория: /var/lib/{имя-вашей-утилиты}/{id}
В качестве rootfs использовать Alpine, но chroot делать на overlayfs:

- lowerdir — базовый rootfs (Alpine)
- upperdir — /var/lib/{имя-утилиты}/{id}/upper
- workdir — /var/lib/{имя-утилиты}/{id}/work
- merged - /var/lib/{имя-утилиты}/{id}/merged
  
Запускаемая команда становится PID=1 внутри контейнера и утилита ждёт её завершения (foreground)
Опционально:
1) Настроить cgroups для ограничения ресурсов контейнера (CPU, память, IO).
2) Внутри контейнера монтировать /proc для корректной работы утилит типа ps

## Введение и подготовка окружения

Все нижеперечисленное я выполнял на арендованной vps, поэтому для начала настроил ssh доступ, создал рабочую директорию `container` в домашней директории, настроил git репозиторий, подключил vscode для удобной работы.

После скачал `alpine rootfs` - версию latest не брал, взял 3.9.6:

![telegram-cloud-photo-size-2-5355216854361775536-y](https://github.com/user-attachments/assets/760e502f-20dc-4eb2-9f22-e83893d39a35)

Скачиваем распаковываем

```
root@m5:/home/andrey/devops/lab1/container# wget https://dl-cdn.alpinelinux.org/alpine/v3.9/releases/x86_64/alpine-minirootfs-3.9.6-x86_64.tar.gz
root@m5:/home/andrey/devops/lab1/container# mkdir rootfs
root@m5:/home/andrey/devops/lab1/container# tar -xzf alpine-minirootfs-3.9.6-x86_64.tar.gz -C rootfs
```

Проверяем содержимое на адекватность и версию:

```
root@m5:/home/andrey/devops/lab1/container/rootfs# ls
bin  dev  etc  home  lib  media  mnt  opt  proc  root  run  sbin  srv  sys  tmp  usr  var
```

```
root@m5:/home/andrey/devops/lab1/container# cat rootfs/etc/alpine-release
3.9.6
```
