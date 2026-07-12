from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends
from jose import jwt, JWTError
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.database import get_db
from app.repositories.user_repository import UserRepository
from app.services.websocket_manager import ws_manager
import json

router = APIRouter()

def get_ws_user(token: str):
    """Helper to safely decode token during the active WS session."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is not None:
            return int(user_id) if str(user_id).isdigit() else user_id
    except JWTError:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM], options={"verify_exp": False})
            user_id = payload.get("sub")
            if user_id is not None:
                return int(user_id) if str(user_id).isdigit() else user_id
        except JWTError:
            return None
    return None

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db),
):
    # 1. Token validation aur identity extract karna
    user_id = get_ws_user(token)
    if user_id is None:
        await websocket.close(code=4003)
        return

    # 2. Database se unique user object nikalna taake exact User ID aur Admin status pata chal sake
    repo = UserRepository(db)
    user_obj = repo.get_by_id(user_id) if isinstance(user_id, int) else repo.get_by_email(user_id)
    if user_obj is None:
        await websocket.close(code=4004)
        return

    is_admin = bool(user_obj.is_superuser)

    # 3. Connection state maintain karne ke liye hamesha 'user_obj.id' (Integer) use karein
    await ws_manager.connect(user_obj.id, websocket, is_admin=is_admin)

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")

            # 4. CUSTOMER CHAT FLOW -> Har connected Admin ko forward hoga
            if msg_type == "chat" and not is_admin:
                payload = {
                    "type": "chat_message",
                    "from": user_obj.id,  # Admin ko customer ki exact database ID pohnchegi
                    "email": user_obj.email, # UI par render karne ke liye user ka email bhej rahe hain
                    "message": data.get("message"),
                }
                await ws_manager.send_to_admins(payload)

            # 5. ADMIN REPLY FLOW -> Sirf specific target customer ko payload jayega
            elif msg_type == "chat_reply" and is_admin:
                target = data.get("to")  # Yeh target customer ki integer ID honi chahiye frontend se
                if target:
                    try:
                        # Agar target single digit/integer string hai toh convert karein
                        target_id = int(target) if str(target).isdigit() else target
                    except ValueError:
                        target_id = target

                    payload = {
                        "type": "chat_response",
                        "sender": f"Support (Admin #{user_obj.id})",
                        "message": data.get("message"),
                    }
                    await ws_manager.send_personal_message(payload, target_id)

    except WebSocketDisconnect:
        # Connection drop hone par clean up hamesha integer ID se hoga
        ws_manager.disconnect(user_obj.id, websocket)