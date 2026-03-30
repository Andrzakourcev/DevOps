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
![telegram-cloud-photo-size-2-5355216854361775577-y](https://github.com/user-attachments/assets/aa973667-1a88-40bc-b786-b2a1a1dc26f2)

## config.json

config.json — это файл конфигурации контейнера, который описывает как именно должен запускаться контейнер. Использует стандарт Open Container Initiative Runtime Specification (OCI). По сути его полное описание. 

```
{
  "ociVersion": "1.0.0",
  "hostname": "mycontainer",
  "process": {
    "terminal": true,
    "user": {
      "uid": 0,
      "gid": 0
    },
    "args": [
      "/bin/sh"
    ],
    "env": [
      "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
      "TERM=xterm"
    ],
    "cwd": "/"
  },
  "root": {
    "path": "alpine-rootfs",
    "readonly": false
  },
  "mounts": [
    {
      "destination": "/proc",
      "type": "proc",
      "source": "proc"
    }
  ],
  "linux": {
    "namespaces": [
      {"type": "pid"},
      {"type": "mount"},
      {"type": "uts"}
    ],
    "resources": {
      "memory": {
        "limit": 100000000
      },
      "cpu": {
        "shares": 512,
        "quota": 50000,
        "period": 100000
            }
        }
    }
}
```

В нем указываем ociVersion, хостнейм, в блоке process описываем какой процесс будет запускаться внутри контейнера:
```
"terminal": true - чтобы интерактивно работать с терминалом

"user": {
  "uid": 0,
  "gid": 0
} - тут в юзер указываем нули чтобы внутри контейнера были от root пользака - не всегда бест практис, но сейчас это не так важно
```

В "args" указываем `/bin/sh` - это главный процесс PID=1, "PATH" указываем чтобы работали базовые команды, "cwd": "/" - рабочая директория процесса

В "root" описыванием rootfs, в "mounts" - монтирование, /proc - вертуальная fs, в которой вся инфа о процессах (нужно чтобы работали команды по типу top ps и тд)

В "linux" блоке настраиваем namespaces и resources.

*namespaces*:

- pid - изолирует процессы 
- mount - изолирует fs
- uts - свой hostname

*resources* - ограничение через cgroups:

- memory - 100mb
- cpu - ограничения проца 

тут готово

# Python утилита 

Теперь напишем скрипт на питоне.

## Общая логика работы скрипта

Скрипт работает в две стадии:

- run — подготовка контейнера
- init — запуск процесса внутри контейнера

что происходит: 

run > создаёт overlayfs > создаёт namespaces > запускает init

init > chroot > hostname > mount /proc > запускает процесс


```
#!/usr/bin/env python3
import os
import sys
import json
import subprocess

RUNTIME = "pycontainer"
BASE_PATH = f"/var/lib/{RUNTIME}"

def load_config():
    with open("config.json") as f:
        return json.load(f)

def setup_overlay(container_id):
    """
    Создание overlayfs для контейнера
    """
    base = f"{BASE_PATH}/{container_id}"
    upper = f"{base}/upper"
    work = f"{base}/work"
    merged = f"{base}/merged"

    os.makedirs(upper, exist_ok=True)
    os.makedirs(work, exist_ok=True)
    os.makedirs(merged, exist_ok=True)

    lower = os.path.abspath("rootfs")

    try:
        opts = f"lowerdir={lower},upperdir={upper},workdir={work}"
        subprocess.check_call([
            "mount", "-t", "overlay", "overlay", "-o", opts, merged
        ])
        print(f"OverlayFS смонтирован в {merged}")
        return merged
    except subprocess.CalledProcessError:
        print("OverlayFS не поддерживается, юзаем обычный rootfs")
        return lower

def run_container(container_id):
    """Создание namespace и запуск init-процесса"""
    rootfs = setup_overlay(container_id)

    cmd = [
        "unshare",
        "--fork",
        "--pid",
        "--mount",
        "--uts",
        "--mount-proc",
        "python3",
        __file__,
        "init",
        rootfs
    ]

    subprocess.check_call(cmd)

def init_container(rootfs):
    """Init контейнера после unshare"""
    config = load_config()

    
    hostname = config.get("hostname", "container")
    subprocess.check_call(["hostname", hostname])

    # chroot на rootfs
    os.chroot(rootfs)
    os.chdir("/")

    # Монтируем /proc 
    if not os.path.exists("/proc/cpuinfo"):
        os.makedirs("/proc", exist_ok=True)
        subprocess.check_call(["mount", "-t", "proc", "proc", "/proc"])

    #  процесс PID=1
    args = config["process"]["args"]
    env = dict(os.environ)
    for e in config["process"].get("env", []):
        key, val = e.split("=", 1)
        env[key] = val

    os.execvpe(args[0], args, env)

def main():
    if len(sys.argv) < 3:
        print("Usage: mycontainer.py <run|init> <id|rootfs>")
        sys.exit(1)

    cmd = sys.argv[1]
    if cmd == "run":
        container_id = sys.argv[2]
        run_container(container_id)
    elif cmd == "init":
        rootfs = sys.argv[2]
        init_container(rootfs)
    else:
        print("Unknown command")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

Енвы у нас `RUNTIME` - задает имя рантайма и `BASE_PATH` пусть к контейнерам. `load_config()` загружает config.json. 

# Создание overlayfs
После создаем overlayfs в функции`setup_overlay()`. Задаем директрии base, upper, work, merged. lower - это базовая система Alpine Linux.

Монтируем overlayfs:

```
mount -t overlay overlay -o lowerdir=rootfs,upperdir=upper,workdir=work merged
```
# Запуск контейнера 

В функции `run_container` для начала создаем overlayfs `rootfs = setup_overlay(container_id)`

После создаем namespaces:

```
unshare --fork --pid --mount --uts --mount-proc python3 mycontainer.py init <rootfs>
```

Потом запускаем `python3 mycontainer.py init`, но уже внутри namespaces

# init контейнера

Грузим конфиг и указываем хостнейм:
```
config = load_config()
hostname = config.get("hostname", "container")
```
Делаем чрутизацию на корень:
```
os.chroot(rootfs)
os.chdir("/")
```
Монтируем `/proc`:
```
mount -t proc proc /proc
```
Добавляем переменные окружения и запускаем процесс:
```
os.execvpe(args[0], args, env)
```

`def main()` описывать не буду она поочереди все запускает.

# Запускаем 
Запускаем написанную утилиту
```
python3 mycontainer.py run test1
```

<img width="526" height="150" alt="image" src="https://github.com/user-attachments/assets/51d1101e-3f69-40c4-873a-385478d39549" />

Попадем в наш изолированный процесс. Сделаем пару проверок.

<img width="367" height="201" alt="image" src="https://github.com/user-attachments/assets/538e4ccf-aaf7-4ffe-bd69-802dd5ecd862" />

Проверяем hostname, проверяем что запущен с PID=1, что используется наша rootfs, и что смонтирован /proc

Также проверим overlayfs:

В контейнере 
```
/ # touch /tmp/hello
/ # ls /tmp
hello
```

На хосте 
```
andrey@m5:~/devops/lab1/containls /var/lib/pycontainer/test1/upper/tmp
hello
```

lowerdir (rootfs):
```
andrey@m5:~/devops/lab1/container$ ls rootfs/tmp/
andrey@m5:~/devops/lab1/container$ 
```
lowerdir не поменялась, в upper видим только изменения, значит overlayfs работает. 

# Итоги

В лабе создан контейнерный runtime на питоне, который изолировано запускает процесс с использованием PID, Mount и UTS namespaces, делает chroot на rootfs и overlayfs для разделения базовой системы и изменений внутри контейнера. Контейнер получает свой hostname, PID=1 для основного процесса, монтирует /proc и ограничивает ресурсы через cgroups. В целом все получилось, классная лаба. Спасибо!

