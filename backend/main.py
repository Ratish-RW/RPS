import cv2
import mediapipe as mp
import time
import math as math
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
    
def checker(frame,num,lms,moves):
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

    #num = random.randint(0,2)
    #cv2.putText(frame, f"Computer Move: {moves[num]}", (10, 70), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
    #print(f"Computer Move: {moves[num]}")

    if (t_tip < t_joint) and (i_tip < i_joint) and (m_tip < m_joint) and (r_tip < r_joint) and (p_tip < p_joint):
        move = "paper"
        print(f"Your Move: {move}")
        cv2.putText(frame, f"You: {move}", (10, 110), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
        if moves[num] == "paper":
            return 2
        if moves[num] == "rock":
            return 1
        return 0
    elif (t_tip > t_joint) and (i_tip > i_joint) and (m_tip > m_joint) and (r_tip > r_joint) and (p_tip > p_joint):
        move = "rock"
        print(f"Your Move: {move}")
        cv2.putText(frame, f"You: {move}", (10, 110), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
        if moves[num] == "rock":
            return 2
        if moves[num] == "scissor":
            return 1
        return 0
    elif (i_tip < i_joint) and (m_tip < m_joint):
        move = "scissor"
        print(f"Your Move: {move}")
        cv2.putText(frame, f"You: {move}", (10, 110), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
        if moves[num] == "scissor":
            return 2
        if moves[num] == "paper":
            return 1
        return 0
    cv2.putText(frame, f"Wrong Move", (10, 110), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
    return -1


def main():  
    ctime=0
    ptime=0
    cap = cv2.VideoCapture(0)
    detector = HandTrackingDynamic()
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    countdown = 3
    rest_time = 2
    start_time = time.time()
    mode = "countdown"
    moves = ["rock","paper","scissor"]

    user_count = 0
    comp_count = 0
    draw_count = 0

    if not cap.isOpened():
        print("Cannot open camera")
        exit()

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        elapsed = int(time.time() - start_time)
        if mode == "countdown":
            remaining = countdown - elapsed
            if remaining > 0:
                cv2.putText(frame, "Show your move!", (150, 250), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
                cv2.putText(frame, str(remaining), (300, 250), cv2.FONT_HERSHEY_PLAIN, 10, (0, 0, 255), 5)
            else:
                frame = detector.findFingers(frame)
                lmsList = detector.findPosition(frame)
                if len(lmsList) != 0:
                    num = random.randint(0,2)
                    cv2.putText(frame, f"Computer: {moves[num]}", (10, 70), cv2.FONT_HERSHEY_PLAIN, 2, (255, 0, 0), 2)
                    print(f"Computer Move: {moves[num]}")
                    lms = lmsList[0]
                    if len(lms) != 0:
                        f=1
                        r = checker(frame,num,lms,moves)
                        if r == 2:
                            cv2.putText(frame, "It's a Draw!", (10, 150), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 255), 2)
                            draw_count += 1
                        elif r == 1:
                            cv2.putText(frame, "You Win!", (10, 150), cv2.FONT_HERSHEY_PLAIN, 2, (0, 255, 0), 2)
                            user_count += 1
                        elif r == 0:
                            cv2.putText(frame, "Computer Wins!", (10, 150), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                            comp_count += 1
                        else:
                            cv2.putText(frame, "Invalid Move!", (10, 150), cv2.FONT_HERSHEY_PLAIN, 2, (0, 0, 255), 2)
                    ctime = time.time()
                    fps =1/(ctime-ptime)
                    ptime = ctime
                mode = "rest"
                start_time = time.time()
                cv2.putText(frame, str(int(fps)), (10,70), cv2.FONT_HERSHEY_PLAIN,1,(255,0,255),2)
        elif mode == "rest":
            cv2.putText(frame, "Next move!", (150, 250), cv2.FONT_HERSHEY_PLAIN, 1, (0, 255, 0), 2)
            if elapsed >= rest_time:
                mode = "countdown"
                start_time = time.time()
        cv2.putText(frame, f"Score - You: {user_count} Computer: {comp_count} Draws: {draw_count}", (10, 430), cv2.FONT_HERSHEY_PLAIN, 1, (255, 255, 0), 2)
        # frame = detector.findFingers(frame)
        # lmsList = detector.findPosition(frame)
        #print(f"Len: {len(lmsList)}")
        # if len(lmsList)!=0:
        #     #print(lmsList[0])
        #     lms = lmsList[0]
        #     #print(lmsList[0])
        #     if len(lmsList[0])!=0:
        #         print(f"Checker: {checker(lmsList[0])}")

        #     ctime = time.time()
        #     fps =1/(ctime-ptime)
        #     ptime = ctime

        # cv2.putText(frame, str(int(fps)), (10,70), cv2.FONT_HERSHEY_PLAIN,3,(255,0,255),3)

#gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        cv2.imshow('frame', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cap.release()
    cv2.destroyAllWindows()
                
if __name__ == "__main__":
    main()