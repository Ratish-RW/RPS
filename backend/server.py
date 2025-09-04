from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from werkzeug.utils import secure_filename
import base64
import os
import cv2
import mediapipe as mp
import math
import random

class HandTrackingDynamic:
    def __init__(self, mode=False, maxHands=2, detectionCon=0.5, trackCon=0.5):
        self.__mode__   =  mode
        self.__maxHands__   =  maxHands
        self.__detectionCon__   =   detectionCon
        self.__trackCon__   =   trackCon
        self.handsMp = mp.solutions.hands
        self.hands = self.handsMp.Hands()
        self.mpDraw= mp.solutions.drawing_utils
        self.tipIds = [4, 8, 12, 16, 20]

    def findFingers(self, frame, draw=True):
        imgRGB = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        self.results = self.hands.process(imgRGB)  
        if self.results.multi_hand_landmarks: 
            for handLms in self.results.multi_hand_landmarks:
                if draw:
                    self.mpDraw.draw_landmarks(frame, handLms,self.handsMp.HAND_CONNECTIONS)

        return frame

    def findPosition( self, frame, handNo=0, draw=True):
        xList =[]
        yList =[]
        bbox = []
        self.lmsList=[]
        if self.results.multi_hand_landmarks:
            myHand = self.results.multi_hand_landmarks[handNo]
            for id, lm in enumerate(myHand.landmark):
            
                h, w, c = frame.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                xList.append(cx)
                yList.append(cy)
                self.lmsList.append([id, cx, cy])
                if draw:
                    cv2.circle(frame,  (cx, cy), 5, (255, 0, 255), cv2.FILLED)

            xmin, xmax = min(xList), max(xList)
            ymin, ymax = min(yList), max(yList)
            bbox = xmin, ymin, xmax, ymax
            print( "Hands Keypoint")
            print(bbox)
            if draw:
                cv2.rectangle(frame, (xmin - 20, ymin - 20),(xmax + 20, ymax + 20),
                               (0, 255 , 0) , 2)

        return self.lmsList, bbox
    
    def findFingerUp(self):
        fingers=[]

        if self.lmsList[self.tipIds[0]][1] > self.lmsList[self.tipIds[0]-1][1]:
            fingers.append(1)
        else:
            fingers.append(0)

        for id in range(1, 5):            
            if self.lmsList[self.tipIds[id]][2] < self.lmsList[self.tipIds[id]-2][2]:
                fingers.append(1)
            else:
                fingers.append(0)
    
        return fingers

    def findDistance(self, p1, p2, frame, draw= True, r=15, t=3):
         
        x1 , y1 = self.lmsList[p1][1:]
        x2, y2 = self.lmsList[p2][1:]
        cx , cy = (x1+x2)//2 , (y1 + y2)//2

        if draw:
              cv2.line(frame,(x1, y1),(x2,y2) ,(255,0,255), t)
              cv2.circle(frame,(x1,y1),r,(255,0,255),cv2.FILLED)
              cv2.circle(frame,(x2,y2),r, (255,0,0),cv2.FILLED)
              cv2.circle(frame,(cx,cy), r,(0,0.255),cv2.FILLED)
        len= math.hypot(x2-x1,y2-y1)

        return len, frame , [x1, y1, x2, y2, cx, cy]
    
detector = HandTrackingDynamic()
    
def checker(lms,moves):
    #print(lms)
    t_tip = lms[3][2]
    t_joint = lms[1][2]
    i_tip = lms[7][2]
    i_joint = lms[5][2]
    m_tip = lms[11][2]
    m_joint = lms[9][2]
    r_tip = lms[15][2]
    r_joint = lms[13][2]
    p_tip = lms[19][2]
    p_joint = lms[17][2]

    num = random.randint(0,2)
    comp_move = moves[num]
    #print(f"Computer Move: {moves[num]}")

    if (t_tip < t_joint) and (i_tip < i_joint) and (m_tip < m_joint) and (r_tip < r_joint) and (p_tip < p_joint):
        player_move = "paper"
        print(player_move)
        if comp_move == "paper":
            emit("result",{"outcome":"Tie","computer_move":comp_move,"player_move":player_move})
        elif comp_move == "rock":
            emit("result",{"outcome":"Player Wins","computer_move":comp_move,"player_move":player_move})
        else:
            emit("result",{"outcome":"Computer Wins","computer_move":comp_move,"player_move":player_move})
    elif (t_tip > t_joint) and (i_tip > i_joint) and (m_tip > m_joint) and (r_tip > r_joint) and (p_tip > p_joint):
        player_move = "rock"
        print(player_move)
        if comp_move == "rock":
            emit("result",{"outcome":"Tie","computer_move":comp_move,"player_move":player_move})
        elif comp_move == "scissor":
            emit("result",{"outcome":"Player Wins","computer_move":comp_move,"player_move":player_move})
        else:
            emit("result",{"outcome":"Computer Wins","computer_move":comp_move,"player_move":player_move})
    elif (i_tip < i_joint) and (m_tip < m_joint):
        player_move = "scissor"
        print(player_move)
        if comp_move == "scissor":
            emit("result",{"outcome":"Tie","computer_move":comp_move,"player_move":player_move})
        elif comp_move == "paper":
            emit("result",{"outcome":"Player Wins","computer_move":comp_move,"player_move":player_move})
        else:
            emit("result",{"outcome":"Computer Wins","computer_move":comp_move,"player_move":player_move})
    else:
        emit("result",{"outcome":"Invalid Move","computer_move":comp_move,"player_move":"Invalid Move"})

def detect_hand(frame):
    frame = detector.findFingers(frame)
    lmsList = detector.findPosition(frame)
    if len(lmsList)!=0:
        moves = ["rock", "paper", "scissor"]
        lms = lmsList[0]
        if len(lms)>20:
            checker(lms, moves)
        else:
            emit("result",{"outcome":"No Hand Detected","computer_move":"N/A","player_move":"N/A"})
    else:
        emit("result",{"outcome":"No Hand Detected","computer_move":"N/A","player_move":"N/A"})

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

UPLOAD_FOLDER = "uploads"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER 


@socketio.on("game")
def handle_image(data):
    image_data = data.split(",")[1]  
    file_path = os.path.join(UPLOAD_FOLDER, "frame.jpg")

    with open(file_path, "wb") as f:
        f.write(base64.b64decode(image_data))

    frame = cv2.imread(file_path)
    if frame is not None:
        detect_hand(frame)
    

if __name__ == "__main__":
     socketio.run(app, host="0.0.0.0", port=5000)
