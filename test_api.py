import urllib.request
import json
import ssl

def register():
    url = "http://127.0.0.1:5000/api/auth/register"
    data = json.dumps({
        "name": "Test User",
        "email": "test@test.com",
        "phone": "9999999999",
        "mpin": "1234"
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            print("Register:", response.read().decode())
    except Exception as e:
        print("Register Error:", str(e))
        if hasattr(e, 'read'):
            print(e.read().decode())

def login():
    url = "http://127.0.0.1:5000/api/auth/login"
    data = json.dumps({
        "phone": "9999999999",
        "mpin": "1234"
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req) as response:
            print("Login:", response.read().decode())
    except Exception as e:
        print("Login Error:", str(e))
        if hasattr(e, 'read'):
            print(e.read().decode())

register()
login()
