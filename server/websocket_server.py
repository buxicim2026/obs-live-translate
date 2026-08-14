"""WebSocket服务器 - 向浏览器源推送字幕"""
import asyncio
import json
import logging

import websockets

logger = logging.getLogger(__name__)


class SubtitleWebSocketServer:
    def __init__(self, host="127.0.0.1", port=9559):
        self.host = host
        self.port = port
        self._server = None
        self._clients = set()
        self._subtitle_buffer = []

    async def _handler(self, websocket):
        """处理单个WebSocket连接"""
        self._clients.add(websocket)
        logger.info(f"浏览器源已连接 (当前连接数: {len(self._clients)})")

        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self._handle_message(websocket, data)
                except json.JSONDecodeError:
                    pass
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            self._clients.discard(websocket)
            logger.info(f"浏览器源已断开 (当前连接数: {len(self._clients)})")

    async def _handle_message(self, websocket, data):
        """处理来自客户端的消息"""
        msg_type = data.get("type", "")

        if msg_type == "ping":
            await websocket.send(json.dumps({"type": "pong"}))
        elif msg_type == "get_status":
            await websocket.send(
                json.dumps(
                    {
                        "type": "status",
                        "clients": len(self._clients),
                        "server_running": True,
                    }
                )
            )
        elif msg_type == "get_config":
            from config import load_config

            cfg = load_config()
            # 不返回API Key
            cfg.pop("api_key", None)
            await websocket.send(
                json.dumps({"type": "config", "data": cfg})
            )
        elif msg_type == "update_config":
            from config import load_config, save_config

            cfg = load_config()
            update_data = data.get("data", {})
            for key, value in update_data.items():
                if key in cfg:
                    cfg[key] = value
            save_config(cfg)
            await websocket.send(
                json.dumps({"type": "config_saved", "success": True})
            )

    async def broadcast_subtitle(self, text, is_final=True):
        """向所有客户端广播字幕"""
        if not self._clients:
            return

        message = json.dumps(
            {
                "type": "subtitle",
                "text": text,
                "is_final": is_final,
                "timestamp": asyncio.get_event_loop().time(),
            },
            ensure_ascii=False,
        )

        disconnected = set()
        for client in self._clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
            except Exception as e:
                logger.error(f"发送字幕失败: {e}")
                disconnected.add(client)

        self._clients -= disconnected

    async def broadcast_status(self, status_data):
        """向客户端广播状态更新"""
        if not self._clients:
            return
        message = json.dumps(
            {"type": "status_update", "data": status_data}, ensure_ascii=False
        )
        disconnected = set()
        for client in self._clients:
            try:
                await client.send(message)
            except websockets.exceptions.ConnectionClosed:
                disconnected.add(client)
        self._clients -= disconnected

    async def start(self):
        self._server = await websockets.serve(
            self._handler, self.host, self.port
        )
        logger.info(f"WebSocket服务器已启动: ws://{self.host}:{self.port}")

    async def stop(self):
        if self._server:
            self._server.close()
            await self._server.wait_closed()
        for client in self._clients:
            try:
                await client.close()
            except Exception:
                pass
        self._clients.clear()
