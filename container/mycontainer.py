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