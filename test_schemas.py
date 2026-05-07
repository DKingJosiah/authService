import sys
import traceback
sys.path.append('.')
from app.schemas import User
from datetime import datetime
try:
    u = User(
        id="123", email="test@test.com", first_name="Aaaa", last_name="Bbbb",
        username="Cccc", is_active=True, is_verified=True, 
        created_at=None, updated_at=datetime.utcnow(), last_login_at=None
    )
    print(u.model_dump())
    print("SUCCESS")
except Exception as e:
    traceback.print_exc()
