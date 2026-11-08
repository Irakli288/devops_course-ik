#!/usr/bin/env bash
# Доставка статического ресурса на devops-vm
# Использование: scripts/deploy.sh [--dry-run]
set -euo pipefail

REMOTE="devops"                       # псевдоним из ~/.ssh/config (ПР № 5, шаг 1.6)
REMOTE_DIR="/var/www/devops-site"
SITE_URL="https://devops.local"
CA_CERT="${HOME}/devops.crt"
REPO_ROOT="$(git rev-parse --show-toplevel)"   # требование 2: работает из любого каталога
LOCAL_DIR="${REPO_ROOT}/site/"

die() { echo "deploy: $*" >&2; exit 1; }

# 1. Разбор аргумента --dry-run (требование 1)
DRY_RUN=""
case "${1:-}" in
  "")        ;;
  --dry-run) DRY_RUN="--dry-run" ;;
  *)         die "неизвестный аргумент '$1'. Использование: $0 [--dry-run]" ;;
esac

# 2. Проверки до доставки (требования 4 и 5)
[[ -f "${LOCAL_DIR}index.html" ]] || die "нет файла site/index.html, доставка отменена"
if ! git -C "$REPO_ROOT" diff --quiet || ! git -C "$REPO_ROOT" diff --cached --quiet; then
  die "в репозитории есть незафиксированные изменения, доставка отменена"
fi
COMMIT="$(git -C "$REPO_ROOT" rev-parse --short HEAD)"

# 3. Синхронизация (требования 3, 8, 9): одно SSH-соединение, без запроса пароля
rsync -az --itemize-changes --delete --chmod=D755,F644 ${DRY_RUN} \
  -e "ssh -o BatchMode=yes -o ConnectTimeout=5" \
  "$LOCAL_DIR" "${REMOTE}:${REMOTE_DIR}/"

# 4. При --dry-run завершение без проверки доступности
if [[ -n "$DRY_RUN" ]]; then
  echo "deploy: пробный запуск, сервер не изменён (коммит ${COMMIT})"
  exit 0
fi

# 5. Проверка доступности с проверкой сертификата (требование 6)
if ! curl -fsS --max-time 10 --cacert "$CA_CERT" -o /dev/null "$SITE_URL/"; then
  die "ресурс ${SITE_URL} недоступен после доставки"
fi
echo "deploy: доставлен коммит ${COMMIT}"   # требование 7
