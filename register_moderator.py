"""
Для регистрации модератора закомментировать строки в serializers.py
    is_staff = serializers.BooleanField(default=False, required=False)
    is_superuser = serializers.BooleanField(default=False, required=False)
"""
from requests import post


url = "http://127.0.0.1:8000/api/register/"
data = {
    "password": "222",
    "username": "moderator_Jane",
    "first_name": "Jane",
    "last_name": "Doe",
    "email": "jane.doe@example.com",
    "is_staff": "true"
}

response = post(url, data=data)


if response.status_code == 201:
    print("User created successfully:", response.json())
else:
    print("Error:", response.json())