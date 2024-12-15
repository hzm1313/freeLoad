from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List
import ollama
import json

app = FastAPI()

# 连接管理器 - 管理所有的websocket连接
