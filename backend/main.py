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

# Default common items for suggestions
DEFAULT_COMMON_ITEMS = [
    "Молоко", "Хліб", "Яйця", "Масло", "Сир", "Сметана", "Кефір", "Йогурт",
    "Курка", "Свинина", "Яловичина", "Риба", "Ковбаса", "Сосиски",
    "Картопля", "Морква", "Цибуля", "Часник", "Помідори", "Огірки", "Капуста",
    "Перець", "Баклажани", "Кабачки", "Буряк", "Гриби", "Салат", "Зелень",
    "Яблука", "Банани", "Апельсини", "Лимони", "Виноград", "Груші",
    "Рис", "Гречка", "Макарони", "Борошно", "Цукор", "Сіль", "Олія",
    "Кава", "Чай", "Печиво", "Шоколад", "Цукерки",
    "Вода", "Сік", "Кетчуп", "Майонез", "Гірчиця", "Оцет",
    "Мило", "Шампунь", "Зубна паста", "Туалетний папір", "Серветки",
    "Порошок", "Миючий засіб", "Губки"
]

def load_common_items():
    if os.path.exists(COMMON_ITEMS_FILE):
        with open(COMMON_ITEMS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return DEFAULT_COMMON_ITEMS

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

    # Add to common items if new
    common_items = load_common_items()
    if request.name not in common_items:
        common_items.append(request.name)
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
                common_items.append(request.name)
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
    if len(q) < 2:
        return []
    common_items = load_common_items()
    q_lower = q.lower()
    suggestions = [item for item in common_items if q_lower in item.lower()]
    return suggestions[:10]

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
