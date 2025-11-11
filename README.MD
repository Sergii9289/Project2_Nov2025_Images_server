# 🖼️ Upload Server

Простий HTTP-сервер на Python для завантаження зображень через `multipart/form-data`.

## 🚀 Запуск

```bash
python services/backend/src/app.py

## Завантаження картинки з PowerShell
& "C:\Windows\System32\curl.exe" -X POST http://localhost:8000/upload/ -F "file=@D:/4.jpg"