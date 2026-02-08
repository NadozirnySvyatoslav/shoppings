# Список покупок

Онлайн додаток для створення та спільного використання списків покупок.

**Demo:** https://shoppings.ndev.online

## Можливості

- Створення списків покупок з унікальними посиланнями
- Спільний доступ - поділіться посиланням і інші бачитимуть зміни в реальному часі
- Підказки товарів при введенні (60+ популярних товарів)
- Відмітка куплених товарів
- Редагування пунктів
- Прогрес-бар виконання
- Збереження відвіданих списків в браузері
- PWA - встановлюється як мобільний додаток
- Адаптивний дизайн для мобільних пристроїв

## Технології

- **Backend:** FastAPI + WebSocket
- **Frontend:** React + Vite
- **Стилі:** CSS (без фреймворків)
- **Зберігання:** JSON файли

## Встановлення

### Вимоги

- Python 3.10+
- Node.js 18+
- Nginx

### Backend

```bash
cd backend
pip install fastapi uvicorn websockets python-multipart
python -m uvicorn main:app --host 0.0.0.0 --port 8100
```

### Frontend

```bash
cd frontend
npm install
npm run build
```

### Systemd сервіс

```ini
[Unit]
Description=Shopping List API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/shopping-list/backend
ExecStart=/usr/bin/python3 -m uvicorn main:app --host 0.0.0.0 --port 8100
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Nginx

```nginx
server {
    server_name shoppings.ndev.online;

    root /root/shopping-list/frontend/dist;
    index index.html;

    location /api {
        proxy_pass http://127.0.0.1:8100;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 86400;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

## API

| Метод | Endpoint | Опис |
|-------|----------|------|
| POST | `/api/lists` | Створити список |
| GET | `/api/lists/{id}` | Отримати список |
| POST | `/api/lists/{id}/items` | Додати товар |
| PATCH | `/api/lists/{id}/items/{item_id}` | Відмітити куплено |
| PUT | `/api/lists/{id}/items/{item_id}` | Редагувати товар |
| DELETE | `/api/lists/{id}/items/{item_id}` | Видалити товар |
| GET | `/api/suggestions?q=` | Підказки товарів |
| WS | `/api/ws/{id}` | WebSocket для оновлень |

## Ліцензія

MIT
