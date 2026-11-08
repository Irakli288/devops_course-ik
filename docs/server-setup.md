# Конфигурация виртуальной машины devops-vm

Документ позволяет восстановить конфигурацию сервера со снимка `01-clean-install`.
Все команды выполняются от имени `devops` (после шага 4) или `student` (до шага 4) с `sudo`.

> Стенд. Роль VirtualBox выполняет Docker на рабочей машине `host-pc`: «виртуальная машина»
> devops-vm — контейнер Ubuntu 24.04 с systemd в роли PID 1, сеть Host-only — bridge-сеть
> `hostonly` (192.168.56.0/24), снимки состояния — образы `devops-vm-snap:<имя>` (`docker commit`).
> Параметры ниже даны и для VirtualBox, и для стенда.

## 1. Параметры машины

| Параметр | VirtualBox | Стенд |
|---|---|---|
| Имя | devops-vm | контейнер `devops-vm`, hostname `devops-vm` |
| ОС | Ubuntu Server 24.04 LTS (64-bit) | образ `ubuntu:24.04` + systemd, openssh-server, ufw |
| Память / ядра | 2048 МБ / 2 | общие с хостом (4 vCPU, 16 ГБ) |
| Диск | 25 ГБ, динамический | слой overlayfs контейнера |
| Пользователь при установке | student (группа sudo) | student (группа sudo) |

Запуск стенда со снимка:

```bash
docker run -d --name devops-vm --hostname devops-vm --privileged --cgroupns=host \
  -v /sys/fs/cgroup:/sys/fs/cgroup:rw --tmpfs /run --tmpfs /run/lock \
  --network hostonly --ip 192.168.56.101 devops-vm-snap:01-clean-install
```

## 2. Сетевые интерфейсы

| Адаптер | Тип | Адрес | Назначение |
|---|---|---|---|
| 1 | NAT | 10.0.2.15 (VirtualBox) | выход в интернет, проброс порта SSH |
| 2 | Host-only | 192.168.56.101/24 | доступ с хоста по имени devops.local (ПР № 6) |

На стенде один интерфейс `eth0` 192.168.56.101/24 выполняет обе роли: шлюз 192.168.56.1
(хост) выпускает трафик в интернет через NAT Docker.

## 3. Правило проброса портов

| Имя | Протокол | Адрес хоста | Порт хоста | Порт гостя |
|---|---|---|---|---|
| ssh | TCP | 127.0.0.1 | 2222 | 22 → **2222** после задания 2 |

На стенде правило реализовано socat на хосте:

```bash
socat TCP-LISTEN:2222,bind=127.0.0.1,fork,reuseaddr TCP:192.168.56.101:2222 &
```

## 4. Учётные записи

| Имя | Группы | Аутентификация по SSH |
|---|---|---|
| student | student, sudo | запрещена (`AllowUsers devops`), только консоль |
| devops | devops, sudo, users | только ключ ed25519 `~/.ssh/devops_vm` (хост) |
| root | — | вход запрещён (`PermitRootLogin no`) |

```bash
sudo adduser devops                 # задать пароль (нужен для sudo)
sudo usermod -aG sudo devops
# на хосте:
ssh-keygen -t ed25519 -C "devops-vm-key" -f ~/.ssh/devops_vm
ssh-copy-id -i ~/.ssh/devops_vm.pub -p 2222 devops@127.0.0.1
```

Права: `~/.ssh` — 700, `~/.ssh/authorized_keys` — 600.

`~/.ssh/config` на хосте:

```
Host devops
    HostName 127.0.0.1
    Port 2222
    User devops
    IdentityFile ~/.ssh/devops_vm
    IdentitiesOnly yes

Host devops.local
    Port 2222
    User devops
    IdentityFile ~/.ssh/devops_vm
    IdentitiesOnly yes
```

## 5. Служба SSH

Основной файл `/etc/ssh/sshd_config` не изменяется (копия — `sshd_config.backup`).
Директивы — в `/etc/ssh/sshd_config.d/99-hardening.conf`:

```
Port 2222
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes
PermitEmptyPasswords no
MaxAuthTries 3
LoginGraceTime 30
AllowUsers devops
X11Forwarding no
ClientAliveInterval 300
ClientAliveCountMax 2
```

Порядок применения (текущую сессию не закрывать, проверять в новом терминале):

```bash
grep -r PasswordAuthentication /etc/ssh/sshd_config.d/   # нет ли 50-cloud-init.conf с "yes"
sudo sshd -t && sudo sshd -T | grep -Ei '^(port|permitrootlogin|passwordauthentication|maxauthtries|allowusers)'
sudo systemctl disable --now ssh.socket   # иначе порт 22 задаёт сокет systemd
sudo systemctl enable --now ssh.service
sudo systemctl restart ssh
sudo ss -tlnp | grep sshd                 # 0.0.0.0:2222
```

После этого изменить в правиле проброса порт гостя на 2222.

## 6. Правила межсетевого экрана

Политики: `deny (incoming)`, `allow (outgoing)`, `deny (routed)`; журналирование `medium`.

| Порт | Действие | Комментарий |
|---|---|---|
| 2222/tcp | LIMIT IN | SSH rate-limited |
| 80/tcp | ALLOW IN | HTTP |
| 443/tcp | ALLOW IN | HTTPS |

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw limit 2222/tcp comment 'SSH rate-limited'   # ДО включения!
sudo ufw allow 80/tcp comment 'HTTP'
sudo ufw allow 443/tcp comment 'HTTPS'
sudo ufw enable
sudo ufw logging medium
```

Не использовать `ufw allow ssh` — это порт 22 из `/etc/services`.

## 6а. Имена

- хост: `/etc/hosts` — `192.168.56.101 devops.local`;
- сервер: `sudo hostnamectl set-hostname devops-vm`, в `/etc/hosts` строка
  `127.0.1.1 devops-vm.devops.local devops-vm`; `hostname -f` → `devops-vm.devops.local`.

## 7. Снимки состояния

| Снимок | Момент создания |
|---|---|
| 01-clean-install | после установки ОС, `apt upgrade`, до любых настроек |
| 02-keys-configured | после задания 1: пользователь devops, ключ, `~/.ssh/config` |
| 03-ssh-hardened | после задания 2: 99-hardening.conf, порт 2222, ssh.service |

Стенд: `docker commit devops-vm devops-vm-snap:<имя>`, список — `docker image ls devops-vm-snap`.

## Проверка

```bash
~/scripts/audit.sh; echo $?    # 0
```

## 8. Веб-сервер

- Пакет: `nginx` из репозитория Ubuntu (`sudo apt install -y nginx`), версия 1.24.0.
  На стенде перед запуском удалён `/usr/sbin/policy-rc.d` (запрет запуска служб в образе Docker),
  а в `/etc/nginx/sites-available/default` закомментирована строка `listen [::]:80` (IPv6 отключён).
- Стандартный ресурс отключён: `sudo rm /etc/nginx/sites-enabled/default` (файл в sites-available сохранён).
- Конфигурация ресурса: `/etc/nginx/sites-available/devops-site`, ссылка в `/etc/nginx/sites-enabled/devops-site`:

```nginx
server {
    listen 80;
    server_name devops.local;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl;
    server_name devops.local;
    ssl_certificate     /etc/ssl/certs/devops.crt;
    ssl_certificate_key /etc/ssl/private/devops.key;
    ssl_protocols       TLSv1.2 TLSv1.3;
    root /var/www/devops-site;
    index index.html;
    location / {
        try_files $uri $uri/ =404;
    }
    error_page 404 /404.html;
    access_log /var/log/nginx/devops-site.access.log;
    error_log /var/log/nginx/devops-site.error.log;
}
```

Применение: `sudo nginx -t && sudo systemctl reload nginx` (не restart).

- Каталог ресурса: `/var/www/devops-site`, владелец `devops:devops`, каталоги 755, файлы 644
  (`sudo mkdir -p /var/www/devops-site && sudo chown -R devops:devops /var/www/devops-site`).
  Содержимое доставляется из каталога `site/` репозитория сценарием `scripts/deploy.sh`.
- Сертификат: `/etc/ssl/certs/devops.crt` (root:root, 644); ключ: `/etc/ssl/private/devops.key` (root:root, 600).
  Срок действия 365 дней. Команда формирования:

```bash
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/devops.key -out /etc/ssl/certs/devops.crt \
  -subj "/CN=devops.local" -addext "subjectAltName=DNS:devops.local"
```

- Хост: копия сертификата для проверки — `scp devops:/etc/ssl/certs/devops.crt ~/devops.crt`;
  проверка — `curl --cacert ~/devops.crt -I https://devops.local`.
- Снимок состояния: `04-nginx-https`.
