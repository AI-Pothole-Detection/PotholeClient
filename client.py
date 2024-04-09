import cv2
import torch
from ultralytics import YOLO
import time
import requests
import numpy as np
import imutils
import os
import asyncio
import threading
import json
import time
from glob import glob
import ctypes
from PIL import Image, ImageTk
from tkinter.font import families
import customtkinter as ctk
import tkinter as tk
import tkintermapview
import math
from matplotlib.path import Path
import socket
from threading import Thread
import playsound
from CTkListbox import *
from geopy.geocoders import Nominatim
import geopy
from geopy.extra.rate_limiter import RateLimiter
import pandas as pd
from tkinter import filedialog

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")

class DraggableCircle:
    def __init__(self, canvas, x, y, radius, color, app):
        self.x = x
        self.y = y
        self.canvas = canvas
        self.app = app
        self.circle = canvas.create_oval(x - radius, y - radius, x + radius, y + radius, fill=color)
        self.radius = radius
        self.canvas.tag_bind(self.circle, '<B1-Motion>', self.drag)
        self.canvas.tag_bind(self.circle, '<ButtonRelease-1>', self.release)

    def drag(self, event):
        x, y = event.x, event.y
        self.x = x
        self.y = y
        self.canvas.coords(self.circle, x - self.radius, y - self.radius, x + self.radius, y + self.radius)

    def release(self, event):
        pass

class PotholeDetection:
    """
    This class is the main class for the pothole detection system.
    First, a popup will appear with a textbox and a dropdown. The textbox will be used to input 
    the URL to the video stream. The dropdown will be used to select the model to use for detection.
    
    The user can then click the "Start" button to start the detection process. Once pressed, the window
    will close and the detection will start.
    """
    
    def __init__(self):
    
        '''
        The UI should have two parts, the camera selection option and the model selection option.
        
        The camera selection option should have a dropdown menu with the available cameras, and an option for streaming from link.
        If the streaming option is selected, a textbox should appear for the user to input the URL.
        
        The model selection option should have a dropdown menu with the available models.
        
        The start button should start the detection process.
        '''
        
        self.root = ctk.CTk()
        self.root.title("Pothole Detection")
        self.root.geometry("700x150")
        self.root.resizable(False, False)
        
        # turn off maximize button
        self.root.attributes("-toolwindow", 1)
        
        # Set corner icon to png
        self.icon = Image.open("C:\\Users\\Lumi\\Documents\\PotholeClient\\pothole.png")
        self.icon = ImageTk.PhotoImage(self.icon)
        self.root.iconphoto(True, self.icon)
        
        self.reload_icon = Image.open("C:\\Users\\Lumi\\Documents\\PotholeClient\\icons8-refresh-ios-17-filled\\icons8-refresh-100.png")
        self.reload_icon = ctk.CTkImage(self.reload_icon)
        
        fontObj = ctk.CTkFont("Helvetica", 24)
        smallerFont = ctk.CTkFont("Helvetica", 16)
        
        # Camera selection
        camera_label = ctk.CTkLabel(self.root, text="Video Feed:", font=fontObj)
        camera_label.grid(row=0, column=0, sticky=ctk.W, padx=5, pady=15)

        self.cameras = []  # Replace with your actual cameras

        self.cameras.append("Stream")
        # cameras.append("Camera 0")
        
        index = 0
        while True:
            try:
                cap = cv2.VideoCapture(index)
                if not cap.read()[0]:
                    break
                else:
                    self.cameras.append(f"Camera {index}")
                cap.release()
                index += 1
            except:
                break
   
        def on_camera_change(event):
            # This function will be called when the camera selection changes
            if self.camera_var.get() == "Stream":
                space.grid_remove()
                self.url_entry.grid()  # Show the URL entry field
            else:
                # url_entry.pack_forget()  # Hide the URL entry field
                # make url field invisible
                self.url_entry.grid_remove()
                space.grid(row=0, column=2, padx=60, pady=5)
        
        # make dropdown (with no typing allowed)
        self.camera_var = ctk.StringVar()
        camera_dropdown = ctk.CTkComboBox(self.root, variable=self.camera_var, values=self.cameras, 
                                          state="readonly", font=smallerFont, command=on_camera_change, width=200)
        camera_dropdown.grid(row=0, column=1, padx=5, pady=5)
        camera_dropdown.set(self.cameras[0])

        self.url_entry = ctk.CTkEntry(self.root, font=smallerFont, width=300, placeholder_text="Enter URL Here")
        self.url_entry.grid(row=0, column=2, padx=5, pady=5)
        
        
        # make empty frame
        space = ctk.CTkFrame(self.root, width=self.url_entry.winfo_width(), height=self.url_entry.winfo_height())



        # Model selection
        model_label = ctk.CTkLabel(self.root, text="Model:", font=fontObj)
        model_label.grid(row=1, column=0, sticky=tk.W, padx=15, pady=15)

        self.model_path = "C:\\Users\\Lumi\\Documents\\PotholeClient\\"
        self.models = [opt.split("\\")[-1][:-3] for opt in glob("C:\\Users\\Lumi\\Documents\\PotholeClient\\*.pt")] # Replace with your actual models
        self.model_var = ctk.StringVar()
        model_dropdown = ctk.CTkComboBox(self.root, variable=self.model_var, values=self.models, state="readonly", font=smallerFont, width=200)
        model_dropdown.set(self.models[0])
        model_dropdown.grid(row=1, column=1, padx=5, pady=5)

        # Start button
        start_button = ctk.CTkButton(self.root, text="Start", command=self.main, font=smallerFont)
        start_button.grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # make window appear on top
        self.root.attributes("-topmost", True)
           
        self.root.mainloop()
        
    def main(self):
        self.url = self.url_entry.get()
        self.cam_name = self.camera_var.get()
        self.model_name = self.model_var.get()
        
        self.cam = None
        
        self.alert_tab_on = False
        self.settings_tabview = None
        
        # model parameters
        self.conf = 0.25
        self.lane_detection = False
        self.pothole_detection = False
        self.old_pothole_detection = False
        
        # alert parameters
        self.opacity = 0.5
        self.alert_sound = False
        self.delay = 5
        self.left_right_alert = True
        self.alert_width = 30
        
        # video parameters
        self.show_potholes = True
        self.show_lane = True
        self.show_fps = False
        
        self.init_camera()

        self.root.destroy()
        
        self.stream = ctk.CTk()
        self.stream.title("Pothole Detection")
        self.stream.geometry("900x700")

        self.tabview = ctk.CTkTabview(self.stream, command=self.on_tab_change)
        self.tabview.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)

        stream_tab = self.tabview.add("Video Feed")
        self.map_tab = self.tabview.add("Map")

        self.stream_canvas = ctk.CTkCanvas(stream_tab, width=800, height=600)
        self.stream_canvas.grid(row=0, column=0, padx=(130,0))

        self.button_frame = ctk.CTkFrame(stream_tab, width = 800, height = 100)
        self.button_frame.grid(row = 1, column = 0, padx = (130,0), pady = 5, sticky="ew")

        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(1, weight=1)
        self.button_frame.grid_columnconfigure(2, weight=1)

        # I want two switches and a button in a row across the bottom
        detection_switch = ctk.CTkSwitch(self.button_frame, text="Pothole Detection", command=self.set_pothole_detection)
        detection_switch.grid(row=0, column = 0, padx = (20, 50), pady = 5, sticky="w")

        lane_switch = ctk.CTkSwitch(self.button_frame, text="Lane Setting", command=self.set_lane_detection)
        lane_switch.grid(row=0, column = 1, padx = (50, 50), pady = 5)

        settings_button = ctk.CTkButton(self.button_frame, text = "Settings", command = self.create_settings_window)
        settings_button.grid(row=0, column=2, padx = (50, 20), pady = 5, sticky="e")
        

        # For setting the lane, let's create a draggable trapezoid
        self.tl_circle = DraggableCircle(self.stream_canvas, 300, 300, 10, 'black', self)
        self.tr_circle = DraggableCircle(self.stream_canvas, 500, 300, 10, 'black', self)
        self.bl_circle = DraggableCircle(self.stream_canvas, 50, 580, 10, 'black', self)
        self.br_circle = DraggableCircle(self.stream_canvas, 750, 580, 10, 'black', self)


        # Map Tab
        self.map_widget = tkintermapview.TkinterMapView(self.map_tab, width=700, height=700)
        self.map_widget.grid(row=0, column=0)
        
        self.map_widget.set_position(28.602337, -81.200369)
        self.map_widget.set_zoom(15)
        
        self.pothole_markers = {}
        
        self.map_widget.add_right_click_menu_command(label="Add Pothole", command=self.add_pothole_thread, pass_coords=True)
        
        self.map_interaction_frame = ctk.CTkFrame(self.map_tab)
        self.map_interaction_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.pothole_dict = {}
        self.pothole_buttons = {}
        
        # self.search_button = ctk.CTkButton(self.map_interaction_frame, text="Select Region", command=self.draw_region)
        # self.search_button.grid(row=0, column=0, padx=5, pady=(10, 5))
        
        self.pothole_list = ctk.CTkScrollableFrame(self.map_interaction_frame, width=275, height=500)
        self.pothole_list.grid(row=1, column=0, padx=5, pady=5, sticky="ew")
        
        self.save_button = ctk.CTkButton(self.map_interaction_frame, text="Generate Report", command=self.generate_report_thread)
        self.save_button.grid(row=2, column=0, padx=5, pady=5)
        
        thread = Thread(target=self.get_potholes_from_server)
        thread.start()
        
        self.stream.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.detection_cycle()
        
    def generate_report_thread(self):
        thread = Thread(target=self.generate_report)
        thread.daemon = True
        thread.start()
        
    def generate_report(self):
        
        self.save_button.configure(state="disabled")
        
        pothole_df = pd.DataFrame(columns=["ID", "Latitude", "Longitude", "Address"])
        
        geolocator = Nominatim(user_agent="Nancy Amandi", timeout= 10)
        rgeocode = RateLimiter(geolocator.reverse, min_delay_seconds=0.1)
        
        for pothole_id, x in self.pothole_dict.items():
            lat, long = x
            
            location = rgeocode((lat, long))
            
            pothole_df.loc[len(pothole_df)] = [pothole_id, lat, long, location.address]
            
        # create filedialog
        file_path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], initialfile="pothole_report")
            
        pothole_df.to_csv(file_path, index=False)
        
        # draw on the bottom of the tab Report Generated!
        report_label = ctk.CTkLabel(self.map_tab, text="Report Generated!")
        report_label.grid(row=1, column=1, padx=5, pady=5)
        
        # wait for 5 seconds
        time.sleep(5)
        
        # remove the label
        report_label.destroy()
        
        self.save_button.configure(state="normal")
        
    def draw_region(self):
        """
        This function will allow the user to draw a region on the map to select potholes.
        """
        self.map_widget.add_left_click_map_command(self.draw_region_callback)
        
    def draw_region_callback(self, coords):
        """
        This function will be called when the user clicks on the map to draw a region.
        """
        if "region" in self.__dict__:
            self.map_widget.delete_shape(self.region)
            
        self.region = self.map_widget.draw_polygon(coords, fill="blue", alpha=0.5)
        
            
    def add_pothole_thread(self, coords):
        thread = Thread(target=self.add_pothole, args=(coords[0], coords[1]))
        thread.start()
        
    def add_pothole(self, lat, long):
        url = "https://aipotholeapi.onrender.com/potholes:report"
        
        data = {
            "latitude": lat,
            "longitude": long
        }
        
        response = requests.post(url, json=data)
        
        if response.json()["type"] == "success":
            pothole_id = response.json()["data"]["message"].split(" ")[-1][:-1]
            
            marker = self.map_widget.set_marker(lat, long, text=pothole_id)
            
            self.pothole_markers[pothole_id] = marker
            self.pothole_dict[pothole_id] = (lat, long)
            
            pothole_frame = ctk.CTkFrame(self.pothole_list, width=200, height=50)
            pothole_frame.grid(padx=5, pady=5, sticky="ew")
            
            pothole_delete_button = ctk.CTkButton(pothole_frame, text="X", command=lambda id=pothole_id: self.delete_pothole_thread(id), fg_color="red", hover_color="red", width=10)
            pothole_delete_button.grid(row=0, column=0, padx=5, pady=5)
            
            pothole_label = ctk.CTkLabel(pothole_frame, text=f"ID {pothole_id}: {lat}, {long}")
            pothole_label.grid(row=0, column=1, padx=5, pady=5)
            
            self.pothole_buttons[pothole_id] = pothole_frame
            
        
    def get_potholes_from_server(self):
        url = "https://aipotholeapi.onrender.com/potholes?minLat=24.718891&minLong=-87.964571&maxLat=31.832765&maxLong=-80.137198"
        
        response = requests.get(url)

        potholes = response.json()["data"]["result"]
        
        for pothole in potholes:
            marker = self.map_widget.set_marker(pothole["lat"], pothole["long"], text=pothole["id"])

            self.pothole_markers[pothole["id"]] = marker
            self.pothole_dict[pothole["id"]] = (pothole["lat"], pothole["long"])
            
            pothole_frame = ctk.CTkFrame(self.pothole_list, width=200, height=50)
            pothole_frame.grid(padx=5, pady=5, sticky="ew")     
            
            pothole_delete_button = ctk.CTkButton(pothole_frame, text="X", command=lambda id=pothole["id"]: self.delete_pothole_thread(id), fg_color="red", hover_color="red", width=10)
            pothole_delete_button.grid(row=0, column=0, padx=5, pady=5)
            
            pothole_label = ctk.CTkLabel(pothole_frame, text=f"ID {pothole['id']}: {pothole['lat']}, {pothole['long']}")
            pothole_label.grid(row=0, column=1, padx=5, pady=5)
            
            self.pothole_buttons[pothole["id"]] = pothole_frame
            
    def delete_pothole_thread(self, id):
        thread = Thread(target=self.delete_pothole, args=(id,))
        thread.start()
            
    def delete_pothole(self, id):
        url = f"https://aipotholeapi.onrender.com/potholes?id={id}"
        
        response = requests.delete(url)
        
        
        if response.json()["type"] == "success":
            self.pothole_markers[id].delete()
            del self.pothole_markers[id]
            del self.pothole_dict[id]
            
            self.pothole_buttons[id].destroy()
            del self.pothole_buttons[id] 

            # self.map_widget.delete_all_marker()
            
            # for key in self.pothole_dict:
            #     self.map_widget.set_marker(self.pothole_dict[key][0], self.pothole_dict[key][1], text=key)
            
            
            
        
    def on_tab_change(self):
        if self.tabview.get() == "Map":
            self.old_pothole_detection = self.pothole_detection
            self.pothole_detection = False
        else:
            self.pothole_detection = self.old_pothole_detection
        
    def create_settings_window(self):
        
        old_lane_detection = self.lane_detection
        
        # Turn off lane detection
        self.lane_detection = False
        
        settings_window = ctk.CTkToplevel(self.stream)
        
        settings_window.title("Settings")
        settings_window.geometry("400x200")
        
        self.settings_tabview = ctk.CTkTabview(settings_window)
        self.settings_tabview.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        detection_tab = self.settings_tabview.add("Detection")
        alert_tab = self.settings_tabview.add("Alert")
        video_tab = self.settings_tabview.add("Video")
        
        # Detection Tab
        detection_frame = ctk.CTkFrame(detection_tab)
        detection_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        confidence_label = ctk.CTkLabel(detection_frame, text="Confidence:")
        confidence_label.grid(row=0, column=0, padx=5, pady=5)
        
        confidence_slider = ctk.CTkSlider(detection_frame, from_=1, to=100, orientation=tk.HORIZONTAL, command=self.set_confidence)
        confidence_slider.set(25)
        confidence_slider.grid(row=0, column=1, padx=5, pady=5)
        
        self.confidence_number = ctk.CTkLabel(detection_frame, text=f"{confidence_slider.get()}%")
        self.confidence_number.grid(row=0, column=2, padx=5, pady=5)
        
        show_detection_label = ctk.CTkLabel(detection_frame, text="Show Detections:")
        show_detection_label.grid(row=1, column=0, padx=5, pady=5)
        
        show_detection_switch = ctk.CTkSwitch(detection_frame, command=self.set_show_potholes, text="")
        show_detection_switch.select()
        show_detection_switch.grid(row=1, column=1, padx=5, pady=5)
        
        model_dropdown_label = ctk.CTkLabel(detection_frame, text="Model:")
        model_dropdown_label.grid(row=2, column=0, padx=5, pady=5)
        
        self.model_dropdown = ctk.CTkComboBox(detection_frame, values=self.models, state="readonly", width=150, command=self.change_model_button_state)
        self.model_dropdown.set(self.model_name)
        
        self.model_dropdown.grid(row=2, column=1, padx=5, pady=5)
        
        self.change_model_button = ctk.CTkButton(detection_frame, text="", image=self.reload_icon, command=self.change_model, width=20)
        self.change_model_button.grid(row=2, column=2, padx=5, pady=5)
        
        if self.model_name == self.models[0]:
            self.change_model_button.configure(state="disabled")
            
        # Alert Tab
        mute_alert_label = ctk.CTkLabel(alert_tab, text="Alert Sound:")
        mute_alert_label.grid(row=0, column=0, padx=5, pady=5)
        
        mute_alert_switch = ctk.CTkSwitch(alert_tab, command=self.set_alert_sound, text="")
        mute_alert_switch.deselect()
        mute_alert_switch.grid(row=0, column=1, padx=5, pady=5)
        
        opacity_label = ctk.CTkLabel(alert_tab, text="Alert Opacity:")
        opacity_label.grid(row=1, column=0, padx=5, pady=5)
        
        opacity_slider = ctk.CTkSlider(alert_tab, from_=1, to=100, orientation=tk.HORIZONTAL, command=self.set_transparency)
        opacity_slider.set(50)
        opacity_slider.grid(row=1, column=1, padx=5, pady=5)
        
        self.opacity_number = ctk.CTkLabel(alert_tab, text=f"{opacity_slider.get()}%")
        self.opacity_number.grid(row=1, column=2, padx=5, pady=5)
        
        delay_label = ctk.CTkLabel(alert_tab, text="Alert Delay:")
        delay_label.grid(row=2, column=0, padx=5, pady=5)
        
        delay_slider = ctk.CTkSlider(alert_tab, from_=1, to=10, orientation=tk.HORIZONTAL, command=self.set_delay)
        delay_slider.set(5)
        delay_slider.grid(row=2, column=1, padx=5, pady=5)
        
        self.delay_number = ctk.CTkLabel(alert_tab, text=f"{delay_slider.get()} s")
        self.delay_number.grid(row=2, column=2, padx=5, pady=5)
        
        alert_width_label = ctk.CTkLabel(alert_tab, text="Alert Width:")
        alert_width_label.grid(row=3, column=0, padx=5, pady=5)
        
        alert_width_slider = ctk.CTkSlider(alert_tab, from_=10, to=200, orientation=tk.HORIZONTAL, command=self.set_alert_width)
        alert_width_slider.set(30)
        alert_width_slider.grid(row=3, column=1, padx=5, pady=5)
        
        self.alert_width_number = ctk.CTkLabel(alert_tab, text=f"{alert_width_slider.get()} px")
        self.alert_width_number.grid(row=3, column=2, padx=5, pady=5)
        
        left_right_alert_label = ctk.CTkLabel(alert_tab, text="Lane Side Alerts:")
        left_right_alert_label.grid(row=4, column=0, padx=5, pady=5)
        
        left_right_alert_switch = ctk.CTkSwitch(alert_tab, command=self.set_left_right_alert, text="")
        left_right_alert_switch.select()
        left_right_alert_switch.grid(row=4, column=1, padx=5, pady=5)        
        
        # Video Tab
        video_frame = ctk.CTkFrame(video_tab)
        video_frame.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
        
        fps_label = ctk.CTkLabel(video_frame, text="Show FPS:")
        fps_label.grid(row=0, column=0, padx=5, pady=5)
        
        fps_switch = ctk.CTkSwitch(video_frame, command=self.set_show_fps, text="")
        fps_switch.deselect()
        fps_switch.grid(row=0, column=1, padx=5, pady=5)
        
        lane_label = ctk.CTkLabel(video_frame, text="Show Lane:")
        lane_label.grid(row=1, column=0, padx=5, pady=5)
        
        lane_switch = ctk.CTkSwitch(video_frame, command=self.set_show_lane, text="")
        lane_switch.select()
        lane_switch.grid(row=1, column=1, padx=5, pady=5)
        
        camera_label = ctk.CTkLabel(video_frame, text="Cameras:")
        camera_label.grid(row=2, column=0, padx=5, pady=5)
        
        self.camera_dropdown = ctk.CTkComboBox(video_frame, values=self.cameras, state="readonly", width=200)
        self.camera_dropdown.set(self.cam_name)
        self.camera_dropdown.grid(row=2, column=1, padx=5, pady=5)
        
        self.refresh_camera_button = ctk.CTkButton(video_frame, image=self.reload_icon, text="", command=self.change_camera, width=20)
        self.refresh_camera_button.grid(row=2, column=2, padx=5, pady=5)
        
        # Make the settings window appear on top
        settings_window.attributes("-topmost", True)
        
        self.lane_detection = old_lane_detection

    def change_camera(self):
        def set_url(url):
            self.url = url
            url_popup.destroy()
            
        state = self.camera_dropdown.get()
        
        self.cam_name = state
        
        # if the camera is a stream, create a popup to enter the URL
        if state == "Stream":
            url_popup = ctk.CTkToplevel(self.stream)
            url_popup.title("Enter URL")
            url_popup.geometry("300x100")
            
            url_label = ctk.CTkLabel(url_popup, text="Enter URL:")
            url_label.grid(row=0, column=0, padx=5, pady=5)
            
            url_entry = ctk.CTkEntry(url_popup, placeholder_text="Enter URL Here")
            url_entry.grid(row=0, column=1, padx=5, pady=5)
            
            url_button = ctk.CTkButton(url_popup, text="Submit", width=30, command=lambda: set_url(url_entry.get()))
            url_button.grid(row=1, column=1, padx=5, pady=5)
        
        self.init_camera()
        
    def set_show_fps(self):
        self.show_fps = not self.show_fps
        
    def change_model_button_state(self, state):        
        if state != self.model_name:
            self.change_model_button.configure(state="normal")
        else:
            self.change_model_button.configure(state="disabled")
        
    def change_model(self):
        self.model_name = self.model_dropdown.get()
        
        self.model = YOLO(self.model_path + self.model_name, verbose=False)
        
    def set_confidence(self, val):
        self.conf = int(val) / 100
        
        self.confidence_number.configure(text=f"{int(val)}%")
        
    def set_lane_detection(self):
        self.lane_detection = not self.lane_detection

    def set_pothole_detection(self):
        self.pothole_detection = not self.pothole_detection
        
    def set_transparency(self, val):
        self.opacity = int(val) / 100
        
        self.opacity_number.configure(text=f"{int(val)}%")
        
    def set_delay(self, val):
        self.delay = int(val)
        
        self.delay_number.configure(text=f"{int(val)} s")
        
    def set_alert_width(self, val):
        self.alert_width = int(val)
        
        self.alert_width_number.configure(text=f"{int(val)} px")
        
    def set_left_right_alert(self):
        self.left_right_alert = not self.left_right_alert
        
    def set_show_potholes(self):
        self.show_potholes = not self.show_potholes
        
    def set_alert_sound(self):
        self.alert_sound = not self.alert_sound
        
    def set_show_potholes(self):
        self.show_potholes = not self.show_potholes
        
    def set_show_lane(self):
        self.show_lane = not self.show_lane
        
    def init_camera(self):
        # Make sure to release the camera before initializing a new one
        if self.cam is not None:
            self.cam.release()
        
        # initialize the camera
        if self.cam_name == "Stream":
            self.cam_base_name = self.url + "/video"
            self.mode = "stream"
            
            self.cam = cv2.VideoCapture(self.cam_base_name)
            self.cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        else:
            self.cam_base_name = int(self.cam_name.split()[1])
            self.mode = "camera"
            
            self.cam = cv2.VideoCapture(self.cam_base_name)
            
                
        self.model = YOLO(self.model_path + self.model_name + ".pt", verbose=False)
    
    def point_in_trapezoid(self, x, y, tl, tr, bl, br):
        '''
        Check if a point is in a trapezoid by comparing the area of the trapezoid to the sum of the areas of the triangles formed by the point and the trapezoid's vertices.
        '''

        tl_x, tl_y = tl
        tr_x, tr_y = tr
        bl_x, bl_y = bl
        br_x, br_y = br

        # Calculate the area of the quadrilateral
        polygon = Path([(tl_x, tl_y), (tr_x, tr_y), (br_x, br_y), (bl_x, bl_y)])

        return polygon.contains_point((x, y))

        
    def detection_cycle(self):
        # detect potholes

        
        fps_time = time.time()
        delay_time = time.time()
        
        left_side = False
        right_side = False
        
        left_last = 0
        right_last = 0
        #while True:
        
        def get_frame():
            nonlocal fps_time, delay_time, left_side, right_side, left_last, right_last
            
            # Check if settings_tabview is on the alert tab (and open)
            if self.settings_tabview is not None:
                if self.settings_tabview.get() == "Alert" and self.settings_tabview.winfo_exists():
                    self.alert_tab_on = True
                else:
                    self.alert_tab_on = False
            
            ret, frame = self.cam.read()
            
            if not ret:
                self.stream.after(5, get_frame)
                return
                
            
            frame = cv2.resize(frame, (800, 600), interpolation=cv2.INTER_LINEAR)

            if self.pothole_detection:
                
                results = self.model(frame, conf = self.conf, verbose=  False)
                                    
                play_sound = False
                
                for r in results:
                    boxes = r.boxes
                    
                    call_api = False
                        
                    for box in boxes:
                        x1, y1, x2, y2 = box.xyxy[0].detach().cpu().numpy().astype(int)
                        
                        # Check if pothole is at least area 100
                        if (x2 - x1) * (y2 - y1) < 100:
                            continue
                        
                                    

                        mid_box_x = (x1 + x2) // 2
                        mid_box_y = (y1 + y2) // 2
                        
        

                        top_mid_x = (self.tl_circle.x + self.tr_circle.x) // 2
                        top_mid_y = (self.tl_circle.y + self.tr_circle.y) // 2

                        bottom_mid_x = (self.bl_circle.x + self.br_circle.x) // 2
                        bottom_mid_y = (self.bl_circle.y + self.br_circle.y) // 2
                        
                        if not self.point_in_trapezoid(mid_box_x, mid_box_y,
                                                   (self.tl_circle.x, self.tl_circle.y),
                                                    (self.tr_circle.x, self.tr_circle.y),
                                                     (self.br_circle.x, self.br_circle.y),
                                                     (self.bl_circle.x, self.bl_circle.y)
                                                    ):
                            continue

                        
                        call_api = True
                        

                        # check if the pothole is on the left or right side of the road
                        # if x1 < frame.shape[1] // 2 and y1 > frame.shape[0] // 2 and time.time() - left_last > self.delay:
                        #     left_side = True
                        #     left_last = time.time()
                            
                        # if x1 > frame.shape[1] // 2 and y1 > frame.shape[0] // 2 and time.time() - right_last > self.delay:
                        #     right_side = True
                        #     right_last = time.time()

                        # calculate the midline of the road


                        # Subtract the mid_box_x and y from the width and height of the frame

                        # Check if the pothole is on the left or right side of the road
                        if self.point_in_trapezoid(mid_box_x, mid_box_y, 
                                                   (self.tl_circle.x, self.tl_circle.y),
                                                   (top_mid_x, top_mid_y),
                                                    (bottom_mid_x, bottom_mid_y),
                                                    (self.bl_circle.x, self.bl_circle.y)
                                                   ) and time.time() - left_last > self.delay:
                            left_side = True
                            left_last = time.time()
                            play_sound = True

                        if self.point_in_trapezoid(mid_box_x, mid_box_y,
                                                    (top_mid_x, top_mid_y),
                                                    (self.tr_circle.x, self.tr_circle.y),
                                                     (self.br_circle.x, self.br_circle.y),
                                                     (bottom_mid_x, bottom_mid_y)
                                                    ) and time.time() - right_last > self.delay:
                             right_side = True
                             right_last = time.time()
                             play_sound = True
                             
                             
                        # Draw boxes, making sure to account for the resized frame
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                             
                if call_api and time.time() - delay_time > self.delay:
                    delay_time = time.time()
                    api_thread = Thread(target=self.call_pothole_upload)
                    api_thread.daemon = True
                    api_thread.start()
                             
                if play_sound and self.alert_sound:
                    playsound.playsound("alert.mp3")
                             
                if time.time() - left_last > self.delay:
                    left_side = False
                    
                if time.time() - right_last > self.delay:
                    right_side = False

                frame_copy = frame.copy()
                if self.left_right_alert:
                    
                    if left_side:
                        # display red bar on very edge of left side
                        cv2.rectangle(frame_copy, (0, 0), (30, frame.shape[0]), (0, 0, 255), -1)
                    if right_side:
                        # display red bar on very edge of right side
                        cv2.rectangle(frame_copy, (frame.shape[1] - 30, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), -1)
                        
                else:
                    if left_side or right_side:
                        # display red bar on very edge of left side
                        cv2.rectangle(frame, (0, 0), (self.alert_width, frame.shape[0]), (0, 0, 255), -1)
                        cv2.rectangle(frame, (frame.shape[1] - self.alert_width, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), -1)

                frame = cv2.addWeighted(frame_copy, self.opacity, frame, 1 - self.opacity, 0, frame)

            frame_copy = frame.copy()

            # if we are currently on the alert tab of the settings window, update the alert status
            if self.alert_tab_on:
                cv2.rectangle(frame_copy, (0, 0), (self.alert_width, frame.shape[0]), (0, 0, 255), -1)
                cv2.rectangle(frame_copy, (frame.shape[1] - self.alert_width, 0), (frame.shape[1], frame.shape[0]), (0, 0, 255), -1)

            frame = cv2.addWeighted(frame_copy, self.opacity, frame, 1 - self.opacity, 0, frame)

            fps = 1.0 / (time.time() - fps_time)
            fps_time = time.time()
            if self.show_fps:
                cv2.putText(frame, f"FPS: {fps:.2f}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            # cv2.imshow("Pothole Detection View", frame)
            
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)

            if self.lane_detection and self.show_lane:
                overlay = frame.copy()

                # Draw  a polygon on the frame
                cv2.fillPoly(overlay, [np.array([[self.tl_circle.x, self.tl_circle.y], [self.tr_circle.x, self.tr_circle.y], [self.br_circle.x, self.br_circle.y], [self.bl_circle.x, self.bl_circle.y]], np.int32)], (22, 22, 22))

                # Add the overlay to the frame
                cv2.addWeighted(overlay, self.opacity, frame, 1 - self.opacity, 0, frame)
            frame = Image.fromarray(frame)

            frame = ImageTk.PhotoImage(frame)
            
            self.stream_canvas.create_image(0, 0, image=frame, anchor=tk.NW)
            self.stream_canvas.image = frame

            # draw the circles
            if self.lane_detection and self.show_lane:
                self.stream_canvas.tag_raise(self.tl_circle.circle)
                self.stream_canvas.tag_raise(self.tr_circle.circle)
                self.stream_canvas.tag_raise(self.bl_circle.circle)
                self.stream_canvas.tag_raise(self.br_circle.circle)


            self.stream.after(20, get_frame)
            
        get_frame()
        self.stream.mainloop()
            
    def on_close(self):
        self.cam.release()
        self.stream.quit()
        self.stream.destroy()
        
    def get_gps(self):
        # get the gps coordinates
        
        # ip_addr = socket.gethostbyname(socket.gethostname())
        
        # if self.mode == "camera":
        #     gps = requests.get("https://ipapi.co/" + ip_addr + "/json").json()
        #     if "latitude" not in gps:
        #         return {"longitude": 0, "latitude": 0}
            
        #     return {"longitude": gps["longitude"], "latitude": gps["latitude"]}
        
        # else:
        gps = requests.get("http://192.168.139.172:8080/gps.json").json()
        return {"longitude": gps["gps"]["longitude"], "latitude": gps["gps"]["latitude"]}
        
    def call_pothole_upload(self):
        """
        This function will be called when a pothole is detected.
        It will send the longitude and latitude to the server.
        """
        gps_coords = self.get_gps()
        longitude, latitude = gps_coords["longitude"], gps_coords["latitude"]
        
        url = "https://aipotholeapi.onrender.com/potholes:report"

        body = {
            "longitude": longitude,
            "latitude": latitude
        }
        
        response = requests.post(url, json=body)
        # print(response)
        # print(response.text)

if __name__ == "__main__":
    PotholeDetection()
    