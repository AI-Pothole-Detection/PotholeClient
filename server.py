import cv2
import torch
from ultralytics import YOLO
import time
import tkinter as tk
import requests
import numpy as np
import imutils
from simple_websocket_server import WebSocketServer, WebSocket
import os
import websockets
import socket
import asyncio

clients = set()

class TransmitToPhone(WebSocket):
    """
    This class is used to transmit the pothole detection results to the phone.
    The phone will be connected to the same network as the computer running the detection, and
    there will only be one phone connected at a time.
    """
    def __init__(self, server, sock, address):
        super().__init__(server, sock, address)
        
    def handle(self):
        for client in clients:
            client.send_message(self.data)
    
    def connected(self):
        clients.add(self)
    
    def handle_close(self):
        clients.remove(self)

if __name__ == "__main__":
    server = WebSocketServer(str(socket.gethostbyname(socket.gethostname())), 8000, TransmitToPhone)
    print(f"Server started at {str(socket.gethostbyname(socket.gethostname()))}:8000")
    server.serve_forever()