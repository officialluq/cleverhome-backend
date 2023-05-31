from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import mysql.connector

import hashlib

mydb = mysql.connector.connect(
  host="172.17.0.2",
  user="root",
  password="change-me",
  database="sensors"
)

cred_db = mysql.connector.connect(
  host="172.17.0.2",
  user="root",
  password="change-me",
  database="users"
)

mycursor = mydb.cursor()
cred_curs = cred_db.cursor()
app = FastAPI()
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://192.168.1.2:3000",
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
#INSERT INTO credentials (username, password) VALUES("dsds","dsds");


@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.post("/login")
async def root(request: Request):
    response = await request.json()
    username, password = "", ""
    if "username" in response:
        username = response["username"]
    if "password" in response:
        password = response["password"]
    source = password.encode()
    md5 = hashlib.md5(source).hexdigest() # returns a str
    cred_curs.execute(f'SELECT * FROM credentials WHERE UserId = \"{username}\" ')
    res = cred_curs.fetchall()[0]
    if md5 == res[2]:
        print("haslo zgodne")
        return {"token": 'test123'}
    else:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    
@app.post("/register_device")
async def root(request: Request):
    mycursor.execute("SELECT * FROM temperature WHERE name =\'MAIN\' ")
    myresult = mycursor.fetchall()
    print(myresult)
    return myresult[0][1]

@app.get("/temperature")
async def root(request: Request):
    mycursor.execute("SELECT * FROM temperature WHERE name =\'MAIN\' ")
    myresult = mycursor.fetchall()
    print(myresult)
    return myresult[0][1]


@app.get("/stream")
async def root(request: Request):
    mycursor.execute("SELECT * FROM temperature WHERE name =\'MAIN\' ")
    myresult = mycursor.fetchall()
    print(myresult)
    return myresult[0][1]


@app.post("/temperature/{item_id}")
async def root(item_id: str):
    print(item_id)
    mycursor.execute(f"UPDATE temperature SET value = {item_id} WHERE name =\'MAIN\' ")
    myresult = mycursor.fetchall()
    print(myresult)
    return myresult