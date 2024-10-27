#!/bin/sh

set -e  # Останавливаем выполнение при любой ошибке

echo "Применяем все существующие миграции..."
alembic upgrade head

echo "Проверяем наличие изменений в моделях..."
alembic revision --autogenerate -m "Autogenerated migration" || true

# Находим последний созданный файл миграции
migration_file=$(ls -t alembic/versions/*_autogenerated_migration.py | head -n 1 2>/dev/null || echo "")

if [ -z "$migration_file" ]; then
  echo "Файл миграции не найден. Новых изменений нет."
else
  # Проверяем, пуста ли миграция (содержит только pass в upgrade и downgrade)
  if grep -q "pass" "$migration_file"; then
    echo "Пустая миграция обнаружена. Удаляем файл: $migration_file"
    rm "$migration_file"
  else
    echo "Обнаружены изменения. Применяем миграцию..."
    alembic upgrade head
  fi
fi

echo "Все миграции успешно завершены."

# Запуск основного приложения
exec python app.py
