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
    "🥛 Молоко 2.5% 1л": 100,
    "🥛 Молоко 3.2% 1л": 95,
    "🧈 Масло Селянське 200г": 90,
    "🧀 Сир Голландський 200г": 85,
    "🧀 Сир Моцарела 125г": 70,
    "🥛 Кефір 1% 900мл": 80,
    "🍶 Сметана 20% 400г": 85,
    "🥛 Йогурт Активіа 4шт": 90,
    "🧀 Сир кисломолочний 9% 200г": 80,
    "🍦 Морозиво Рудь 500г": 65,
    "🥛 Ряжанка 4% 450г": 60,
    "🧀 Сирки глазуровані 3шт": 85,

    # Хліб
    "🍞 Хліб Тостовий білий": 100,
    "🍞 Хліб Бородинський": 90,
    "🥖 Батон нарізний": 95,
    "🥐 Круасани 4шт": 70,
    "🫓 Лаваш тонкий": 65,
    "🥯 Бублики з маком 4шт": 55,

    # Яйця
    "🥚 Яйця курячі С1 10шт": 100,
    "🥚 Яйця курячі С0 10шт": 85,

    # М'ясо
    "🍗 Філе куряче 1кг": 100,
    "🍗 Гомілки курячі 1кг": 90,
    "🍗 Крильця курячі 1кг": 75,
    "🥩 Свинина ошийок 1кг": 80,
    "🥩 Свинина карбонад 500г": 70,
    "🥩 Яловичина 500г": 65,
    "🍖 Фарш свино-яловичий 500г": 85,
    "🍖 Фарш курячий 500г": 80,
    "🌭 Сосиски Молочні 500г": 90,
    "🥓 Ковбаса Докторська 300г": 85,
    "🥓 Шинка 200г": 70,
    "🥓 Бекон нарізка 150г": 60,

    # Риба
    "🐟 Лосось стейк 300г": 65,
    "🐟 Скумбрія свіжа 1шт": 60,
    "🐟 Тіляпія філе 400г": 55,
    "🦐 Креветки 300г": 50,

    # Овочі
    "🥔 Картопля 2кг": 100,
    "🧅 Цибуля ріпчаста 1кг": 100,
    "🥕 Морква 1кг": 100,
    "🧄 Часник 3шт": 90,
    "🍅 Помідори 1кг": 95,
    "🍅 Помідори чері 250г": 75,
    "🥒 Огірки свіжі 1кг": 95,
    "🥬 Капуста біла 1шт": 80,
    "🥬 Пекінська капуста 1шт": 70,
    "🫑 Перець болгарський 3шт": 80,
    "🥦 Броколі 400г": 60,
    "🥬 Салат Айсберг 1шт": 70,
    "🌿 Укроп пучок": 75,
    "🌿 Петрушка пучок": 70,
    "🧅 Цибуля зелена пучок": 65,
    "🍄 Печериці 400г": 70,
    "🥒 Огірки мариновані 700г": 60,

    # Фрукти
    "🍌 Банани 1кг": 100,
    "🍎 Яблука Голден 1кг": 95,
    "🍊 Апельсини 1кг": 85,
    "🍋 Лимони 3шт": 80,
    "🍇 Виноград 500г": 65,
    "🍐 Груші 1кг": 60,
    "🥝 Ківі 4шт": 55,
    "🍓 Полуниця 400г": 50,
    "🫐 Чорниця 125г": 45,
    "🥭 Манго 1шт": 40,
    "🍑 Персики 500г": 50,

    # Крупи та макарони
    "🍝 Спагеті 500г": 95,
    "🍝 Макарони пір'я 500г": 90,
    "🍝 Локшина яєчна 400г": 70,
    "🍚 Рис довгозернистий 1кг": 90,
    "🌾 Гречка 1кг": 95,
    "🥣 Вівсянка швидкого приготування 500г": 85,
    "🌾 Пшоно 500г": 50,
    "🍚 Булгур 500г": 45,

    # Бакалія
    "🧂 Сіль кухонна 1кг": 70,
    "🍬 Цукор білий 1кг": 80,
    "🌻 Олія соняшникова 1л": 95,
    "🫒 Олія оливкова 500мл": 60,
    "🍚 Борошно пшеничне 2кг": 75,

    # Соуси
    "🍅 Кетчуп Торчин 450г": 90,
    "🥫 Майонез Королівський смак 400г": 85,
    "🫙 Гірчиця 200г": 55,
    "🧴 Соєвий соус 250мл": 60,
    "🍝 Томатна паста 200г": 70,
    "🫙 Аджика 200г": 50,

    # Консерви
    "🥫 Кукурудза Бондюель 340г": 75,
    "🥫 Горошок зелений 400г": 75,
    "🐟 Тунець у власному соку 185г": 65,
    "🐟 Шпроти в олії 150г": 55,
    "🥫 Квасоля в томаті 400г": 50,
    "🥫 Оливки 300г": 55,

    # Напої
    "💧 Вода Моршинська 1.5л": 95,
    "💧 Вода Боржомі 0.5л": 70,
    "🧃 Сік Садочок 1л": 85,
    "🧃 Сік Rich 1л": 75,
    "☕ Кава мелена Lavazza 250г": 80,
    "☕ Кава розчинна Nescafe 100г": 75,
    "🍵 Чай Lipton 25 пак": 85,
    "🍵 Чай зелений 25 пак": 70,
    "🥤 Coca-Cola 1.5л": 65,
    "🥤 Fanta 1.5л": 55,

    # Солодощі
    "🍫 Шоколад Milka 100г": 90,
    "🍫 Шоколад Roshen 100г": 85,
    "🍪 Печиво Орео 154г": 85,
    "🍪 Печиво вівсяне 300г": 75,
    "🍬 Цукерки Рошен 200г": 70,
    "🍭 Льодяники Chupa Chups": 60,
    "🧇 Вафлі Світоч 150г": 65,
    "🍰 Рулет шоколадний": 55,
    "🧁 Кекс з родзинками": 50,

    # Снеки
    "🥜 Горішки мікс 200г": 70,
    "🥜 Арахіс солоний 200г": 65,
    "🍿 Попкорн для мікрохвильовки": 55,
    "🥨 Крекер TUC 100г": 60,
    "🥔 Чіпси Lay's 120г": 70,

    # Заморожені
    "🥟 Вареники з картоплею 900г": 80,
    "🥟 Вареники з вишнею 500г": 70,
    "🥟 Пельмені 900г": 75,
    "🍕 Піца 4 сири 350г": 65,
    "🐔 Наггетси курячі 500г": 75,
    "🍟 Картопля фрі 750г": 65,
    "🥦 Овочева суміш заморожена 400г": 55,
    "🍓 Ягоди заморожені 300г": 50,

    # Сніданки
    "🥣 Пластівці Nesquik 500г": 85,
    "🥣 Мюслі з фруктами 400г": 70,
    "🍯 Мед квітковий 400г": 65,
    "🥜 Паста арахісова 340г": 55,
    "🫙 Варення полуничне 400г": 60,
    "🥞 Суміш для млинців 500г": 50,
    "🍞 Тости Fazer": 60,

    # Гігієна
    "🧻 Туалетний папір Zewa 8шт": 100,
    "🧴 Шампунь Head&Shoulders 400мл": 75,
    "🧴 Гель для душу 400мл": 70,
    "🧼 Мило рідке 500мл": 80,
    "🪥 Зубна паста Colgate 100мл": 80,
    "🪥 Зубні щітки 2шт": 60,
    "💆 Серветки вологі 100шт": 85,
    "🧴 Дезодорант": 65,
    "🩹 Пластир набір": 45,

    # Побутова хімія
    "🧺 Порошок Persil 3кг": 75,
    "🧴 Гель для прання 1л": 70,
    "🧴 Засіб для посуду Fairy 500мл": 85,
    "🧹 Губки кухонні 5шт": 75,
    "🗑️ Пакети для сміття 60л 20шт": 80,
    "🧹 Серветки для прибирання 3шт": 60,
    "🧴 Засіб для скла 500мл": 50,

    # Для дітей
    "🧒 Підгузки Pampers 40шт": 70,
    "🧒 Серветки вологі дитячі 72шт": 75,
    "🧃 Сік дитячий Агуша 200мл 3шт": 70,
    "🍼 Пюре фруктове Hipp 100г 4шт": 65,
    "🍪 Печиво дитяче Heinz 60г": 60,

    # Для тварин
    "🐱 Корм для котів Whiskas 400г": 55,
    "🐶 Корм для собак Pedigree 500г": 50,
    "🐱 Наповнювач для котів 5л": 50,
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
        return [item[0] for item in sorted_items[:50]]

    q_lower = q.lower()
    # Filter and sort by popularity
    matching = [(name, count) for name, count in common_items.items() if q_lower in name.lower()]
    matching.sort(key=lambda x: x[1], reverse=True)
    return [item[0] for item in matching[:15]]

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
