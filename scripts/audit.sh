#!/usr/bin/env bash
# Аудит конфигурации devops-vm (ПР № 5)
set -uo pipefail
PASS=0; FAIL=0
check() {
  local desc="$1" expected="$2" actual="$3"
  if [[ "$actual" == "$expected" ]]; then
    echo "  [OK]   $desc"; ((PASS++))
  else
    echo "  [FAIL] $desc (ожидалось: '$expected', получено: '$actual')"; ((FAIL++))
  fi
}

echo "Аудит конфигурации: $(hostname -f), $(date '+%Y-%m-%d %H:%M')"

echo "[1] Служба SSH"
SSHD_T="$(sudo sshd -T)"
check "Вход от имени root запрещён" "no" "$(awk '/^permitrootlogin/{print $2}' <<<"$SSHD_T")"
check "Парольная аутентификация отключена" "no" "$(awk '/^passwordauthentication/{print $2}' <<<"$SSHD_T")"
# TODO 1: порт отличен от 22
SSH_PORT="$(awk '/^port /{print $2; exit}' <<<"$SSHD_T")"
check "Порт SSH отличен от 22 (сейчас ${SSH_PORT:-?})" "yes" "$([[ -n "$SSH_PORT" && "$SSH_PORT" != "22" ]] && echo yes || echo no)"
# TODO 2: MaxAuthTries равно 3
check "MaxAuthTries равно 3" "3" "$(awk '/^maxauthtries/{print $2}' <<<"$SSHD_T")"

echo "[2] Межсетевой экран"
check "Межсетевой экран активен" "active" "$(sudo ufw status | awk '/^Status:/{print $2}')"
# TODO 3: политика по умолчанию для входящего трафика равна deny
check "Политика входящего трафика: deny" "deny" \
  "$(sudo ufw status verbose | grep '^Default:' | sed -E 's/^Default: ([a-z]+) \(incoming\).*/\1/')"

echo "[3] Учётные записи"
awk -F: '$3>=1000 && $3<65534 {printf "  %s (uid=%s)\n",$1,$3}' /etc/passwd

echo "[4] Веб-сервер"
check "Служба nginx активна" "active" "$(systemctl is-active nginx)"
check "Конфигурация nginx корректна" "0" "$(sudo nginx -t >/dev/null 2>&1; echo $?)"
CERT_DAYS="${CERT_DAYS:-30}"
check "Сертификат действует ещё ${CERT_DAYS}+ дней" "0" \
  "$(openssl x509 -checkend $((CERT_DAYS*24*3600)) -noout -in /etc/ssl/certs/devops.crt >/dev/null; echo $?)"
check "Нет файлов o+w в ресурсе, права ключа 600" "0 600" \
  "$(find /var/www/devops-site -perm -o+w | wc -l) $(sudo stat -c '%a' /etc/ssl/private/devops.key)"

echo "Пройдено: $PASS, не пройдено: $FAIL"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
