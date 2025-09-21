# Исправление ошибки установки

## Проблема
При запуске установочного скрипта возникала ошибка:
```
The following packages have unmet dependencies:
 init : PreDepends: systemd-sysv but it is not going to be installed
E: Error, pkgProblemResolver::Resolve generated breaks, this may be caused by held packages.
```

## Причина
В установочном скрипте и Dockerfile был указан несуществующий пакет `systemctl` в списке зависимостей для установки через `apt-get install`.

`systemctl` - это команда для управления systemd сервисами, а не отдельный пакет. Она входит в состав пакета `systemd`, который уже установлен в системе по умолчанию.

## Исправление
Удален `systemctl` из списка пакетов для установки в:
- `install.sh` (строка 62)
- `Dockerfile` (строка 9)

## Как применить исправление

### Если вы уже клонировали репозиторий:
```bash
cd xray-manager-api
git pull origin main
sudo bash install.sh
```

### Если установка все еще не работает:
Попробуйте обновить пакеты и исправить зависимости:
```bash
sudo apt-get update
sudo apt-get install -f
sudo apt-get autoremove
sudo bash install.sh
```

### Альтернативный способ установки:
Если проблемы с зависимостями продолжаются, используйте Docker:
```bash
docker-compose up -d
```

## Статус
✅ **Исправлено** - установочный скрипт и Dockerfile обновлены и должны работать корректно.