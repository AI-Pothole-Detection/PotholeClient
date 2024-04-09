import cv2
import numpy as np

cap = cv2.VideoCapture('rtmp://192.168.1.189/live/stream')

while True:
    ret, frame = cap.read()
    if not ret:
        print('Error: frame not read')
        continue

    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
