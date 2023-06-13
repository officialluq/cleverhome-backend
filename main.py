from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.responses import JSONResponse, FileResponse, Response
from fastapi.encoders import jsonable_encoder
import mysql.connector
import io
import hashlib
try:
    from picamera2 import Picamera2
    from picamera2.encoders import MJPEGEncoder, Quality
    from picamera2.encoders import H264Encoder
    from picamera2.configuration import StreamConfiguration
    from picamera2.outputs import FileOutput
except ImportError:
    ...
from threading import Thread, Condition
import time
import sys
import json

class StreamingOutput(io.BufferedIOBase):
    def __init__(self):
        super().__init__()
        self.frame = b''
        self.buffer = io.BytesIO()
        self.condition = Condition()


    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            # New frame, copy the existing buffer's content and notify all
            # clients it's available
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)
            
    def read(self):
        with self.condition:
            return self.frame
        
buffor = StreamingOutput()
            
mydb = mysql.connector.connect(
  host="192.168.1.2",
  user="root",
  password="change-me",
  database="cleverhome",
  autocommit=True
)

cred_db = mysql.connector.connect(
  host="192.168.1.2",
  user="root",
  password="change-me",
  database="users"
)

mycursor = mydb.cursor()
jsoncursor = mydb.cursor(dictionary=True, buffered=False)
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

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.configure("video")
picam2.start()

def start_streaming():
    picam2.start_recording(MJPEGEncoder(), FileOutput(buffor))
    

#INSERT INTO credentials (username, password) VALUES("dsds","dsds");
# thread = Thread(target=start_streaming)
# thread.start()
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
    

@app.get("/advertise/{device_id}")
async def root(device_id: str):
    mycursor.execute('INSERT INTO notification_list (Name, Description) VALUES ("System", "Detected new device! {}")'.format(device_id))
    myresult = mycursor.fetchall()
    print(myresult)
    return myresult

@app.get("/temperature")
async def root(request: Request):
    mycursor.execute("SELECT * FROM temperature WHERE name =\'MAIN\' ")
    myresult = mycursor.fetchall()
    print(myresult)
    return myresult[0][1]

@app.get("/download")
async def root(request: Request):
    return FileResponse(path="trailer_hd.mp4", filename="video_file.mp4")


@app.get("/show_video")
async def root(request: Request):
    def iterfile():
        with open("trailer_hd.mp4", mode="rb") as file_like:
            yield from file_like
    return StreamingResponse(iterfile(), media_type="video/mp4")


@app.get("/stream")
async def root(request: Request):
    mycursor.execute("SELECT * FROM temperature WHERE name =\'MAIN\' ")
    myresult = mycursor.fetchall()
    print(myresult)
    return myresult[0][1]

@app.get("/get_sensor_reading/{parameter}")
async def root(parameter: str):
    mycursor.execute("SELECT * FROM {param} ORDER BY Date DESC".format(param=parameter))
    myresult = mycursor.fetchall()
    if(myresult):
        if parameter == "activity":
            return myresult[0][1]
        return myresult[0][0]
    else:
        print("There was no data for this parameter: {}".format(parameter))



@app.get("/recording_list")
async def root(request: Request):
    jsoncursor.execute("SELECT * FROM recording_list")
    myresult = jsoncursor.fetchall()
    print(myresult)
    return myresult

@app.get("/notification_list")
async def root(request: Request):
    jsoncursor.execute("SELECT * FROM notification_list")
    myresult = jsoncursor.fetchall()
    print(myresult)
    return myresult


@app.get("/log_list")
async def root(request: Request):
    jsoncursor.execute("SELECT * FROM log_list")
    myresult = jsoncursor.fetchall()
    print(myresult)
    return myresult


@app.get("/latest_notifications")
async def root(request: Request):
    jsoncursor.execute("SELECT * FROM notification_list ORDER BY Date DESC LIMIT 3")
    myresult = jsoncursor.fetchall()
    print(myresult)
    return myresult




@app.get("/device_list")
async def root(request: Request):
    jsoncursor.execute("SELECT * FROM device_list")
    myresult = jsoncursor.fetchall()
    print(myresult)
    return myresult

@app.get("/record")
async def root(request: Request):
    h264_encoder = H264Encoder()
    picam2.start_encoder(h264_encoder,"out11.h264")
    # streams = picam2.camera_configuration()
    # name = picam2.encode_stream_name
    # h264_encoder.output =  FileOutput("out11.h264")
    # h264_encoder.width, h264_encoder.height = streams[name]['size']
    # h264_encoder.format = streams[name]['format']
    # h264_encoder.stride = streams[name]['stride']
    # min_frame_duration = picam2.camera_ctrl_info["FrameDurationLimits"][1].min
    # min_frame_duration = max(min_frame_duration, 33333)
    # h264_encoder.framerate = 1000000 / min_frame_duration
    # h264_encoder._setup(Quality.HIGH)
    # h264_encoder.start()
    time.sleep(10)
    h264_encoder.stop()



@app.get("/camera")
async def root(request: Request):
    headers = {"Age": "0",'Cache-Control': 'no-cache, private','Pragma': 'no-cache'}

    def gen():
        while True:
            frame = buffor.frame
            yield (b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

    return StreamingResponse(gen(), media_type='multipart/x-mixed-replace; boundary=frame', headers=headers)

@app.post("/notify_about/{device_id}/{parameter}/{value}")
async def root(parameter: str, device_id: str, value: str ):
    mycursor.execute("INSERT into {} (Value, DEVICE_ID) VALUES ({}, \'{}\')".format(parameter, value, device_id))
    notify_result = mycursor.fetchall()
    mycursor.execute("SELECT Name from device_list WHERE DEVICE_ID = \'{}\'".format(device_id))
    search_result = mycursor.fetchall()
    if search_result:
        mycursor.execute("INSERT INTO log_list (Name, Description) VALUES (\"{}\", \"Reported {} with {}\")".format(search_result[0][0],parameter , value))
        mycursor.fetchall()
        return Response()
    return Response(status_code=401)
    
    
@app.post("/register_device")
async def root(request: Request):
    req = await request.body()
    dec_req = json.loads(req)
    # print(encoded_req)
    mycursor.execute("INSERT into device_list (Name, DEVICE_ID) VALUES (\'{name}\', \'{enc}\')".format(name=dec_req["name"], enc=dec_req["device_id"]))
    
    # print(myresult)
    # return myresult
    
    
@app.delete("/remove_device")
async def root(request: Request):
    req = await request.body()
    dec_req = json.loads(req)
    print(dec_req)
    mycursor.execute("DELETE FROM device_list WHERE ID = \'{}\'".format(dec_req["id"]))