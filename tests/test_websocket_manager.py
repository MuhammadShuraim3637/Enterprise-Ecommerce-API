import asyncio
from app.services.websocket_manager import WebSocketManager


class FakeWebSocket:
    def __init__(self, fail_send=False):
        self.accepted = False
        self.sent_messages = []
        self.fail_send = fail_send

    async def accept(self):
        self.accepted = True

    async def send_json(self, message):
        if self.fail_send:
            raise Exception("Connection closed unexpectedly")
        self.sent_messages.append(message)


def run_async(coro):
    return asyncio.run(coro)


class TestWebSocketManagerConnect:

    def test_connect_accepts_and_registers_websocket(self):
        manager = WebSocketManager()
        ws = FakeWebSocket()
        run_async(manager.connect(user_id=1, websocket=ws))

        assert ws.accepted is True
        assert 1 in manager.active_connections
        assert ws in manager.active_connections[1]

    def test_connect_multiple_devices_same_user(self):
        manager = WebSocketManager()
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        run_async(manager.connect(user_id=1, websocket=ws1))
        run_async(manager.connect(user_id=1, websocket=ws2))

        assert len(manager.active_connections[1]) == 2


class TestWebSocketManagerDisconnect:

    def test_disconnect_removes_websocket(self):
        manager = WebSocketManager()
        ws = FakeWebSocket()
        run_async(manager.connect(user_id=1, websocket=ws))

        manager.disconnect(user_id=1, websocket=ws)
        assert 1 not in manager.active_connections

    def test_disconnect_keeps_other_devices_of_same_user(self):
        manager = WebSocketManager()
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        run_async(manager.connect(user_id=1, websocket=ws1))
        run_async(manager.connect(user_id=1, websocket=ws2))

        manager.disconnect(user_id=1, websocket=ws1)
        assert 1 in manager.active_connections
        assert ws1 not in manager.active_connections[1]
        assert ws2 in manager.active_connections[1]

    def test_disconnect_nonexistent_user_does_not_crash(self):
        manager = WebSocketManager()
        ws = FakeWebSocket()
        # Ye user kabhi connect hi nahi hua tha
        manager.disconnect(user_id=999, websocket=ws)  # crash nahi hona chahiye


class TestSendPersonalMessage:

    def test_send_personal_message_delivers_to_user(self):
        manager = WebSocketManager()
        ws = FakeWebSocket()
        run_async(manager.connect(user_id=1, websocket=ws))

        run_async(manager.send_personal_message({"type": "test"}, user_id=1))
        assert {"type": "test"} in ws.sent_messages

    def test_send_personal_message_to_nonexistent_user_does_nothing(self):
        manager = WebSocketManager()
        # crash nahi hona chahiye agar user connected hi nahi
        run_async(manager.send_personal_message({"type": "test"}, user_id=999))

    def test_send_personal_message_handles_stale_connection(self):
        manager = WebSocketManager()
        ws_good = FakeWebSocket()
        ws_stale = FakeWebSocket(fail_send=True)
        run_async(manager.connect(user_id=1, websocket=ws_good))
        run_async(manager.connect(user_id=1, websocket=ws_stale))

        # ws_stale exception dega, lekin crash nahi hona chahiye, aur ws_good ko message milna chahiye
        run_async(manager.send_personal_message({"type": "test"}, user_id=1))
        assert {"type": "test"} in ws_good.sent_messages


class TestBroadcast:

    def test_broadcast_sends_to_all_connected_users(self):
        manager = WebSocketManager()
        ws1 = FakeWebSocket()
        ws2 = FakeWebSocket()
        run_async(manager.connect(user_id=1, websocket=ws1))
        run_async(manager.connect(user_id=2, websocket=ws2))

        run_async(manager.broadcast({"type": "order_update", "status": "shipped"}))

        assert {"type": "order_update", "status": "shipped"} in ws1.sent_messages
        assert {"type": "order_update", "status": "shipped"} in ws2.sent_messages

    def test_broadcast_handles_stale_connection_gracefully(self):
        manager = WebSocketManager()
        ws_good = FakeWebSocket()
        ws_stale = FakeWebSocket(fail_send=True)
        run_async(manager.connect(user_id=1, websocket=ws_good))
        run_async(manager.connect(user_id=2, websocket=ws_stale))

        run_async(manager.broadcast({"type": "test"}))
        assert {"type": "test"} in ws_good.sent_messages

    def test_broadcast_with_no_connections_does_not_crash(self):
        manager = WebSocketManager()
        run_async(manager.broadcast({"type": "test"}))  # crash nahi hona chahiye