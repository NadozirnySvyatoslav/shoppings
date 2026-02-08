from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import json
import uuid
import os
from datetime import datetime

app = FastAPI(title="Shopping List API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = "/root/shopping-list/data"
COMMON_ITEMS_FILE = os.path.join(DATA_DIR, "common_items.json")

# Default common items with popularity counter - for family of 2 adults + 2 kids
DEFAULT_COMMON_ITEMS = {
    # Молочка
    "🥛 Молоко": 100,
    "🧈 Масло вершкове": 90,
    "🧀 Сир твердий": 85,
    "🧀 Моцарела": 70,
    "🥛 Кефір": 80,
    "🍶 Сметана": 85,
    "🥛 Йогурт": 90,
    "🧀 Сир кисломолочний": 80,
    "🍦 Морозиво": 65,
    "🥛 Ряжанка": 60,
    "🧀 Сирки глазуровані": 85,

    # Хліб
    "🍞 Хліб білий": 100,
    "🍞 Хліб чорний": 90,
    "🥖 Батон": 95,
    "🥐 Круасани": 70,
    "🫓 Лаваш": 65,
    "🥯 Бублики": 55,

    # Яйця
    "🥚 Яйця": 100,

    # М'ясо
    "🍗 Філе куряче": 100,
    "🍗 Гомілки курячі": 90,
    "🍗 Крильця курячі": 75,
    "🥩 Свинина": 80,
    "🥩 Яловичина": 65,
    "🍖 Фарш": 85,
    "🌭 Сосиски": 90,
    "🥓 Ковбаса": 85,
    "🥓 Шинка": 70,
    "🥓 Бекон": 60,

    # Риба
    "🐟 Лосось": 65,
    "🐟 Скумбрія": 60,
    "🐟 Тіляпія": 55,
    "🦐 Креветки": 50,

    # Овочі
    "🥔 Картопля": 100,
    "🧅 Цибуля": 100,
    "🥕 Морква": 100,
    "🧄 Часник": 90,
    "🍅 Помідори": 95,
    "🍅 Помідори чері": 75,
    "🥒 Огірки": 95,
    "🥬 Капуста біла": 80,
    "🥬 Пекінська капуста": 70,
    "🫑 Перець болгарський": 80,
    "🥦 Броколі": 60,
    "🥬 Салат": 70,
    "🌿 Укроп": 75,
    "🌿 Петрушка": 70,
    "🧅 Цибуля зелена": 65,
    "🍄 Печериці": 70,
    "🥒 Огірки мариновані": 60,

    # Фрукти
    "🍌 Банани": 100,
    "🍎 Яблука": 95,
    "🍊 Апельсини": 85,
    "🍋 Лимони": 80,
    "🍇 Виноград": 65,
    "🍐 Груші": 60,
    "🥝 Ківі": 55,
    "🍓 Полуниця": 50,
    "🫐 Чорниця": 45,
    "🥭 Манго": 40,
    "🍑 Персики": 50,

    # Крупи та макарони
    "🍝 Спагеті": 95,
    "🍝 Макарони": 90,
    "🍝 Локшина": 70,
    "🍚 Рис": 90,
    "🌾 Гречка": 95,
    "🥣 Вівсянка": 85,
    "🌾 Пшоно": 50,
    "🍚 Булгур": 45,

    # Бакалія
    "🧂 Сіль": 70,
    "🍬 Цукор": 80,
    "🌻 Олія соняшникова": 95,
    "🫒 Олія оливкова": 60,
    "🍚 Борошно": 75,

    # Соуси
    "🍅 Кетчуп": 90,
    "🥫 Майонез": 85,
    "🫙 Гірчиця": 55,
    "🧴 Соєвий соус": 60,
    "🍝 Томатна паста": 70,
    "🫙 Аджика": 50,

    # Консерви
    "🥫 Кукурудза консервована": 75,
    "🥫 Горошок зелений": 75,
    "🐟 Тунець консервований": 65,
    "🐟 Шпроти": 55,
    "🥫 Квасоля в томаті": 50,
    "🥫 Оливки": 55,

    # Напої
    "💧 Вода мінеральна": 95,
    "🧃 Сік": 85,
    "☕ Кава мелена": 80,
    "☕ Кава розчинна": 75,
    "🍵 Чай чорний": 85,
    "🍵 Чай зелений": 70,
    "🥤 Coca-Cola": 65,
    "🥤 Fanta": 55,

    # Солодощі
    "🍫 Шоколад": 90,
    "🍪 Печиво": 85,
    "🍬 Цукерки": 70,
    "🍭 Льодяники": 60,
    "🧇 Вафлі": 65,
    "🍰 Рулет": 55,
    "🧁 Кекс": 50,

    # Снеки
    "🥜 Горішки": 70,
    "🥜 Арахіс": 65,
    "🍿 Попкорн": 55,
    "🥨 Крекери": 60,
    "🥔 Чіпси": 70,

    # Заморожені
    "🥟 Вареники": 80,
    "🥟 Пельмені": 75,
    "🍕 Піца заморожена": 65,
    "🐔 Наггетси": 75,
    "🍟 Картопля фрі": 65,
    "🥦 Овочі заморожені": 55,
    "🍓 Ягоди заморожені": 50,

    # Сніданки
    "🥣 Пластівці": 85,
    "🥣 Мюслі": 70,
    "🍯 Мед": 65,
    "🥜 Паста арахісова": 55,
    "🫙 Варення": 60,
    "🥞 Суміш для млинців": 50,

    # Гігієна
    "🧻 Туалетний папір": 100,
    "🧴 Шампунь": 75,
    "🧴 Гель для душу": 70,
    "🧼 Мило": 80,
    "🪥 Зубна паста": 80,
    "🪥 Зубна щітка": 60,
    "💆 Серветки вологі": 85,
    "🧴 Дезодорант": 65,
    "🩹 Пластир": 45,

    # Побутова хімія
    "🧺 Порошок пральний": 75,
    "🧴 Гель для прання": 70,
    "🧴 Засіб для посуду": 85,
    "🧹 Губки кухонні": 75,
    "🗑️ Пакети для сміття": 80,
    "🧹 Серветки для прибирання": 60,
    "🧴 Засіб для скла": 50,

    # Для дітей
    "🧒 Підгузки": 70,
    "🧒 Серветки дитячі": 75,
    "🧃 Сік дитячий": 70,
    "🍼 Пюре дитяче": 65,
    "🍪 Печиво дитяче": 60,

    # Для тварин
    "🐱 Корм для котів": 55,
    "🐶 Корм для собак": 50,
    "🐱 Наповнювач для котів": 50,
}

def load_common_items():
    if os.path.exists(COMMON_ITEMS_FILE):
        with open(COMMON_ITEMS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Migration from old format (list) to new format (dict with counts)
            if isinstance(data, list):
                return {item: 50 for item in data}
            return data
    return DEFAULT_COMMON_ITEMS.copy()

def save_common_items(items):
    with open(COMMON_ITEMS_FILE, "w", encoding="utf-8") as f:
        json.dump(items, f, ensure_ascii=False, indent=2)

class ShoppingItem(BaseModel):
    id: str
    name: str
    completed: bool = False

class ShoppingList(BaseModel):
    id: str
    name: str
    items: list[ShoppingItem] = []
    created_at: str
    updated_at: str

class CreateListRequest(BaseModel):
    name: str

class AddItemRequest(BaseModel):
    name: str

class UpdateItemRequest(BaseModel):
    name: str

class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, list_id: str):
        await websocket.accept()
        if list_id not in self.active_connections:
            self.active_connections[list_id] = []
        self.active_connections[list_id].append(websocket)

    def disconnect(self, websocket: WebSocket, list_id: str):
        if list_id in self.active_connections:
            if websocket in self.active_connections[list_id]:
                self.active_connections[list_id].remove(websocket)

    async def broadcast(self, list_id: str, message: dict):
        if list_id in self.active_connections:
            for connection in self.active_connections[list_id]:
                try:
                    await connection.send_json(message)
                except:
                    pass

manager = ConnectionManager()

def get_list_path(list_id: str) -> str:
    return os.path.join(DATA_DIR, f"{list_id}.json")

def load_list(list_id: str) -> Optional[dict]:
    path = get_list_path(list_id)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None

def save_list(shopping_list: dict):
    path = get_list_path(shopping_list["id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(shopping_list, f, ensure_ascii=False, indent=2)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/lists")
def create_list(request: CreateListRequest):
    list_id = str(uuid.uuid4()).replace("-", "")[:16]
    now = datetime.now().isoformat()
    shopping_list = {
        "id": list_id,
        "name": request.name,
        "items": [],
        "created_at": now,
        "updated_at": now
    }
    save_list(shopping_list)
    return shopping_list

@app.get("/api/lists/{list_id}")
def get_list(list_id: str):
    shopping_list = load_list(list_id)
    if not shopping_list:
        raise HTTPException(status_code=404, detail="List not found")
    return shopping_list

@app.post("/api/lists/{list_id}/items")
async def add_item(list_id: str, request: AddItemRequest):
    shopping_list = load_list(list_id)
    if not shopping_list:
        raise HTTPException(status_code=404, detail="List not found")

    item = {
        "id": str(uuid.uuid4()).replace("-", "")[:12],
        "name": request.name,
        "completed": False
    }
    shopping_list["items"].append(item)
    shopping_list["updated_at"] = datetime.now().isoformat()
    save_list(shopping_list)

    # Add to common items if new, or increment if exists
    common_items = load_common_items()
    if request.name in common_items:
        common_items[request.name] += 1
    else:
        common_items[request.name] = 1
    save_common_items(common_items)

    await manager.broadcast(list_id, {"type": "list_updated", "list": shopping_list})
    return item

@app.patch("/api/lists/{list_id}/items/{item_id}")
async def toggle_item(list_id: str, item_id: str):
    shopping_list = load_list(list_id)
    if not shopping_list:
        raise HTTPException(status_code=404, detail="List not found")

    for item in shopping_list["items"]:
        if item["id"] == item_id:
            item["completed"] = not item["completed"]
            shopping_list["updated_at"] = datetime.now().isoformat()
            save_list(shopping_list)
            await manager.broadcast(list_id, {"type": "list_updated", "list": shopping_list})
            return item

    raise HTTPException(status_code=404, detail="Item not found")

@app.put("/api/lists/{list_id}/items/{item_id}")
async def update_item(list_id: str, item_id: str, request: UpdateItemRequest):
    shopping_list = load_list(list_id)
    if not shopping_list:
        raise HTTPException(status_code=404, detail="List not found")

    for item in shopping_list["items"]:
        if item["id"] == item_id:
            item["name"] = request.name
            shopping_list["updated_at"] = datetime.now().isoformat()
            save_list(shopping_list)

            # Add to common items or increment counter
            common_items = load_common_items()
            if request.name in common_items:
                common_items[request.name] += 1
            else:
                common_items[request.name] = 5  # Start at 5 so it shows in suggestions immediately
            save_common_items(common_items)

            await manager.broadcast(list_id, {"type": "list_updated", "list": shopping_list})
            return item

    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/api/lists/{list_id}/items/{item_id}")
async def delete_item(list_id: str, item_id: str):
    shopping_list = load_list(list_id)
    if not shopping_list:
        raise HTTPException(status_code=404, detail="List not found")

    shopping_list["items"] = [i for i in shopping_list["items"] if i["id"] != item_id]
    shopping_list["updated_at"] = datetime.now().isoformat()
    save_list(shopping_list)

    await manager.broadcast(list_id, {"type": "list_updated", "list": shopping_list})
    return {"status": "deleted"}

@app.get("/api/suggestions")
def get_suggestions(q: str = ""):
    common_items = load_common_items()

    # Filter: show only items with count >= 5 (popular enough) or default items
    filtered_items = {
        name: count for name, count in common_items.items()
        if count >= 5 or name in DEFAULT_COMMON_ITEMS
    }

    if len(q) < 2:
        # Return top popular items sorted by popularity
        sorted_items = sorted(filtered_items.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:50]]

    q_lower = q.lower()
    # Filter and sort by popularity
    matching = [(name, count) for name, count in filtered_items.items() if q_lower in name.lower()]
    matching.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in matching[:15]]

@app.get("/api/popular")
def get_popular(limit: int = 50):
    """Get popular items sorted by usage count (only items with 5+ uses or defaults)"""
    common_items = load_common_items()

    # Filter: show only items with count >= 5 or default items
    filtered_items = {
        name: count for name, count in common_items.items()
        if count >= 5 or name in DEFAULT_COMMON_ITEMS
    }

    sorted_items = sorted(filtered_items.items(), key=lambda x: x[1], reverse=True)
    return [{"name": name, "count": count} for name, count in sorted_items[:limit]]

@app.websocket("/api/ws/{list_id}")
async def websocket_endpoint(websocket: WebSocket, list_id: str):
    await manager.connect(websocket, list_id)
    try:
        while True:
            data = await websocket.receive_text()
            # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(websocket, list_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8100)
