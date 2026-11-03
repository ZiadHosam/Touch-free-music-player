
import asyncio
import hashlib
import json
import secrets
import sqlite3
import re
from pathlib import Path
from websockets.asyncio.server import serve

connected_clients = set()
active_sessions = {}
DB_FILE = Path(__file__).with_name("touchless_users.db")
PBKDF2_ROUNDS = 310_000


def initialize_database():
    with sqlite3.connect(DB_FILE) as db:
        db.execute("""CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            password_salt BLOB NOT NULL,
            password_hash BLOB NOT NULL
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            service TEXT NOT NULL,
            item TEXT NOT NULL,
            action TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now'))
        )""")


def hash_password(password, salt):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ROUNDS)


def authenticate_message(data):
    action = data.get("action")
    if action == "logout":
        active_sessions.pop(str(data.get("session", "")), None)
        return {"ok": True}
    email = str(data.get("email", "")).strip().casefold()
    password = str(data.get("password", ""))
    name = str(data.get("name", "")).strip()

    if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return {"ok": False, "error": "Enter a valid email address."}
    if len(password) < 8:
        return {"ok": False, "error": "Password must be at least 8 characters."}

    with sqlite3.connect(DB_FILE) as db:
        db.row_factory = sqlite3.Row
        row = db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
        if action == "signup":
            if not name:
                return {"ok": False, "error": "Enter your name."}
            if row:
                return {"ok": False, "error": "An account with that email already exists."}
            salt = secrets.token_bytes(16)
            password_hash = hash_password(password, salt)
            cursor = db.execute(
                "INSERT INTO users (email, name, password_salt, password_hash) VALUES (?, ?, ?, ?)",
                (email, name, salt, password_hash),
            )
            user_id = cursor.lastrowid
            session = secrets.token_urlsafe(32)
            active_sessions[session] = user_id
            return {"ok": True, "session": session, "user": {"id": user_id, "email": email, "name": name}}

        if action == "login":
            if not row or not secrets.compare_digest(hash_password(password, row["password_salt"]), row["password_hash"]):
                return {"ok": False, "error": "Email or password is incorrect."}
            session = secrets.token_urlsafe(32)
            active_sessions[session] = row["id"]
            return {"ok": True, "session": session, "user": {"id": row["id"], "email": row["email"], "name": row["name"]}}
    return {"ok": False, "error": "Unsupported account action."}


def history_message(data):
    user_id = active_sessions.get(str(data.get("session", "")))
    action = data.get("action")
    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        return {"ok": False, "error": "Your session has expired. Sign in again."}

    with sqlite3.connect(DB_FILE) as db:
        db.row_factory = sqlite3.Row
        if action == "add":
            service = str(data.get("service", "Other / System media"))[:80]
            item = str(data.get("item", ""))[:160]
            event = str(data.get("event", ""))[:80]
            if not item or not event:
                return {"ok": False, "error": "History entry is incomplete."}
            if not db.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone():
                return {"ok": False, "error": "Account not found."}
            db.execute("INSERT INTO history (user_id, service, item, action) VALUES (?, ?, ?, ?)",
                       (user_id, service, item, event))
            return {"ok": True}
        if action == "list":
            rows = db.execute(
                "SELECT id, service, item, action, created_at FROM history WHERE user_id = ? ORDER BY id DESC LIMIT 100",
                (user_id,),
            ).fetchall()
            return {"ok": True, "items": [dict(row) for row in rows]}
        if action == "delete":
            cursor = db.execute("DELETE FROM history WHERE id = ? AND user_id = ?",
                                (data.get("item_id"), user_id))
            return {"ok": cursor.rowcount > 0, "error": "History item not found." if cursor.rowcount == 0 else None}
        if action == "clear":
            db.execute("DELETE FROM history WHERE user_id = ?", (user_id,))
            return {"ok": True}
    return {"ok": False, "error": "Unsupported history action."}


async def handle_client(websocket):

    connected_clients.add(websocket)
    print("Client connected!")
    #print("Total connected clients:", len(connected_clients))

    try:
        async for message in websocket:

            try:
                data = json.loads(message)
                message_type = data.get("type")

                if message_type in ("auth", "history"):
                    try:
                        result = authenticate_message(data) if message_type == "auth" else history_message(data)
                    except sqlite3.IntegrityError:
                        result = {"ok": False, "error": "An account with that email already exists."}
                    await websocket.send(json.dumps({
                        "type": f"{message_type}_result",
                        "request_id": data.get("request_id"),
                        **result,
                    }))
                    continue

                if message_type in ["gesture", "user"]:

                    print("\nMessage received:")
                    print(json.dumps(data, indent=4))

                    sent_count = 0

                    for client in list(connected_clients):

                        if client != websocket:

                            try:
                                await client.send(json.dumps(data))
                                sent_count += 1

                            except Exception as error:
                                print("Could not forward message:", error)

                    print("Forwarded to", sent_count, "client(s)")

                else:
                    print("Other message:", data)

            except json.JSONDecodeError:
                print("Invalid JSON:", message)

    finally:
        connected_clients.discard(websocket)
        print("Client disconnected!")


async def main():

    initialize_database()

    async with serve(handle_client, "localhost", 8765):

        print("WebSocket server started!")
        print("Address: ws://localhost:8765")

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
