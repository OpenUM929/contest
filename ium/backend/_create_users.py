import requests

# Create users via API
base = "http://localhost:8000"

users_to_create = [
    {"user_type": "elder", "nickname": "김어르신", "welfare_id": "095e3aad-90d1-45bb-8d51-a0d3da15738a"},
    {"user_type": "elder", "nickname": "박어르신", "welfare_id": "095e3aad-90d1-45bb-8d51-a0d3da15738a"},
    {"user_type": "elder", "nickname": "최어르신", "welfare_id": "095e3aad-90d1-45bb-8d51-a0d3da15738a"},
    {"user_type": "youth", "nickname": "김청년", "welfare_id": "095e3aad-90d1-45bb-8d51-a0d3da15738a"},
    {"user_type": "youth", "nickname": "이청년", "welfare_id": "095e3aad-90d1-45bb-8d51-a0d3da15738a"},
    {"user_type": "youth", "nickname": "박청년", "welfare_id": "095e3aad-90d1-45bb-8d51-a0d3da15738a"},
]

created = []
for u in users_to_create:
    try:
        resp = requests.post(f"{base}/api/chat/users", json=u, timeout=10)
        print(f"Created {u['nickname']}: {resp.status_code} - {resp.text}")
        if resp.status_code == 200:
            created.append(resp.json())
    except Exception as e:
        print(f"Error creating {u['nickname']}: {e}")

print(f"\nTotal created: {len(created)}")
