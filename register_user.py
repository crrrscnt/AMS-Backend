from requests import post


url = "http://127.0.0.1:8000/api/register/"
data = {
    "password": "222",
    "username": "user_Rick",
    "first_name": "Richard",
    "last_name": "Roe",
    "email": "dick.roe@example.com"
}

response = post(url, data=data)


if response.status_code == 201:
    print("User created successfully:", response.json())
else:
    print("Error:", response.json())