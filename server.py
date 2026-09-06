import json
import os
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

game_state = {
    "status": "waiting",
    "round": 1,
    "players": {},
}

connected_clients = set()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.add(websocket)
    player_id = str(id(websocket))
    
    game_state["players"][player_id] = {
        "id": player_id,
        "name": f"Player {len(game_state['players']) + 1}",
        "hand": [],
        "bid": None,
        "won": 0,
        "score": 0
    }
    
    await broadcast_state()

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            
            if message.get("type") == "START_GAME":
                if len(game_state["players"]) >= 3:
                    game_state["status"] = "bidding"
                await broadcast_state()
                
            elif message.get("type") == "SUBMIT_BID":
                bid_val = message.get("bid")
                if player_id in game_state["players"]:
                    game_state["players"][player_id]["bid"] = int(bid_val)
                await broadcast_state()
                
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
        if player_id in game_state["players"]:
            del game_state["players"][player_id]
        if len(game_state["players"]) < 3:
            game_state["status"] = "waiting"
        await broadcast_state()

async def broadcast_state():
    state_json = json.dumps(game_state)
    for client in connected_clients:
        try:
            await client.send_text(state_json)
        except Exception:
            pass

if os.path.exists("dist"):
    app.mount("/assets", StaticFiles(directory="dist/assets"), name="assets")

    @app.get("/")
    async def serve_index():
        return FileResponse("dist/index.html")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 5000))
    uvicorn.run(app, host="0.0.0.0", port=port)