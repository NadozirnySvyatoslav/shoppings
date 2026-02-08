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
    # Молочні продукти
    "🥛 Молоко": 100,
    "🧈 Масло вершкове": 90,
    "🧀 Сир твердий": 85,
    "🥛 Кефір": 80,
    "🍶 Сметана": 80,
    "🥛 Йогурт": 95,
    "🧀 Сир кисломолочний": 75,
    "🍦 Морозиво": 70,

    # Хліб та випічка
    "🍞 Хліб білий": 100,
    "🥖 Батон": 90,
    "🍞 Хліб чорний": 85,
    "🥐 Булочки": 75,
    "🥯 Бублики": 60,

    # Яйця
    "🥚 Яйця курячі": 100,

    # М'ясо та риба
    "🍗 Куряче філе": 95,
    "🍗 Курячі гомілки": 85,
    "🥩 Свинина": 80,
    "🥩 Яловичина": 70,
    "🐟 Риба": 75,
    "🌭 Сосиски": 90,
    "🥓 Ковбаса варена": 80,
    "🍖 Фарш": 85,

    # Овочі
    "🥔 Картопля": 100,
    "🧅 Цибуля": 95,
    "🥕 Морква": 95,
    "🧄 Часник": 85,
    "🍅 Помідори": 90,
    "🥒 Огірки": 90,
    "🥬 Капуста": 80,
    "🫑 Перець болгарський": 75,
    "🥦 Броколі": 60,
    "🍆 Баклажани": 55,
    "🥬 Салат": 70,
    "🌿 Зелень (укроп, петрушка)": 80,
    "🍄 Гриби": 65,

    # Фрукти
    "🍌 Банани": 100,
    "🍎 Яблука": 95,
    "🍊 Апельсини": 85,
    "🍋 Лимони": 70,
    "🍇 Виноград": 65,
    "🍐 Груші": 60,
    "🥝 Ківі": 55,
    "🍓 Полуниця": 50,
    "🫐 Чорниця": 45,

    # Крупи та макарони
    "🍝 Макарони": 95,
    "🍚 Рис": 90,
    "🌾 Гречка": 90,
    "🥣 Вівсянка": 85,
    "🌾 Пшоно": 50,

    # Бакалія
    "🧂 Сіль": 60,
    "🍬 Цукор": 75,
    "🌻 Олія соняшникова": 90,
    "🫒 Олія оливкова": 60,
    "🍚 Борошно": 70,

    # Соуси та приправи
    "🍅 Кетчуп": 85,
    "🥫 Майонез": 80,
    "🫙 Гірчиця": 50,
    "🧴 Соєвий соус": 55,
    "🌶️ Перець чорний": 60,
    "🍃 Лавровий лист": 45,

    # Консерви
    "🥫 Консервована кукурудза": 70,
    "🥫 Горошок зелений": 70,
    "🐟 Тунець консервований": 60,

    # Напої
    "💧 Вода мінеральна": 90,
    "🧃 Сік": 85,
    "☕ Кава": 80,
    "🍵 Чай": 85,
    "🥤 Компот": 50,

    # Солодощі
    "🍫 Шоколад": 85,
    "🍪 Печиво": 90,
    "🍬 Цукерки": 75,
    "🍰 Торт": 50,
    "🧁 Кекси": 55,

    # Снеки для дітей
    "🥜 Горішки": 70,
    "🍿 Попкорн": 55,
    "🧀 Сирки солодкі": 80,
    "🥤 Йогурт питний": 85,

    # Заморожені продукти
    "🥟 Вареники": 75,
    "🥟 Пельмені": 70,
    "🍕 Піца заморожена": 65,
    "🐔 Наггетси курячі": 75,
    "🍟 Картопля фрі": 60,

    # Сніданки
    "🥣 Пластівці": 85,
    "🥞 Млинці (суміш)": 55,
    "🍯 Мед": 65,
    "🥜 Арахісова паста": 50,
    "🫙 Варення": 55,

    # Гігієна
    "🧻 Туалетний папір": 95,
    "🧴 Шампунь": 75,
    "🧼 Мило": 80,
    "🪥 Зубна паста": 75,
    "🧹 Серветки вологі": 85,
    "🧷 Підгузки": 60,

    # Побутова хімія
    "🧺 Порошок пральний": 70,
    "🧴 Засіб для миття посуду": 80,
    "🧹 Губки для посуду": 70,
    "🗑️ Пакети для сміття": 75,

    # Для дітей
    "🧃 Сік дитячий": 70,
    "🍼 Пюре фруктове": 65,
    "🍪 Печиво дитяче": 60,
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
    list_id = str(uuid.uuid4())[:8]
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
        "id": str(uuid.uuid4())[:8],
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

            # Add to common items if new
            common_items = load_common_items()
            if request.name not in common_items:
                common_items[request.name] = 1
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

    if len(q) < 2:
        # Return top popular items sorted by popularity
        sorted_items = sorted(common_items.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_items[:15]]

    q_lower = q.lower()
    # Filter and sort by popularity
    matching = [(name, count) for name, count in common_items.items() if q_lower in name.lower()]
    matching.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in matching[:10]]

@app.get("/api/popular")
def get_popular(limit: int = 20):
    """Get popular items sorted by usage count"""
    common_items = load_common_items()
    sorted_items = sorted(common_items.items(), key=lambda x: x[1], reverse=True)
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
