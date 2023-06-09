#!/usr/bin/env python
# coding: utf-8

# In[1]:

import re
import requests
import random
import math
import time
import threading
import os
import pygame
import sys
import numpy as np
import time
import cv2
import os
import imutils
from picamera import PiCamera
from time import sleep
import uuid

camera = PiCamera()
# import pandas as pd
from decouple import config
import csv
import RPi.GPIO as GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

GPIO.setup(18,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)
GPIO.setup(24,GPIO.OUT)

GPIO.setup(16,GPIO.OUT)
GPIO.setup(20,GPIO.OUT)
GPIO.setup(21,GPIO.OUT)

GPIO.setup(17,GPIO.OUT)
GPIO.setup(27,GPIO.OUT)
GPIO.setup(22,GPIO.OUT)

GPIO.setup(13,GPIO.OUT)
GPIO.setup(19,GPIO.OUT)
GPIO.setup(26,GPIO.OUT)
# from dotenv import load_dotenv
# load_dotenv()
GOOGLE_API_KEY = config("GOOGLE_API_KEY")
OPEN_WEATHER_API_KEY = config("OPEN_WEATHER_API_KEY")



# In[2]:

# '''
# Initialising the csv file for traffic data collection
# '''
# header = ['P1', 'P2', 'P3', 'P4', 'Lane1', 'Lane2', 'Lane3', 'Lane4', 'Total']
# with open('../data/4.11-Way-Analysis-Dynamic.csv', 'w', encoding='UTF8', newline='') as f:
#     writer = csv.writer(f)

#     # write the header
#     writer.writerow(header)


# In[3]:

# Default values of signal times
defaultRed = 195
defaultYellow = 5
defaultGreen = 20
defaultMinimum = 10
defaultMaximum = 60

data = []
trustScoreData = []
activePriorityVehicles = []
Emergency = False
displaySkip = False
signals = []
congestion = []
noOfSignals = 4
simTime = 400       # total simulation time
timeElapsed = 0
weightage = 0.33
hotspot_region = False

# In[4]:


currentGreen = 0   # Indicates which signal is green

nextGreen = (currentGreen+1) % noOfSignals

currentYellow = 0   # Indicates whether yellow signal is on or off


# Average times for vehicles to pass the intersection
carTime = 1.5             # 50km/h
bikeTime = 1            # 60km/h
rickshawTime = 2          # 60km/h
busTime = 2.5            # 45km/h
truckTime = 2.5           # 45km/h
ambulanceTime = 1
fireTruckTime = 2
policeCarTime = 1

# In[5]:


# Count of vehicles at a traffic signal
noOfCars = 0
noOfBikes = 0
noOfBuses = 0
noOfTrucks = 0
noOfRickshaws = 0
noOfAmbulances = 0
noOffireTrucks = 0
noOfPoliceCars = 0
noOfLanes = 2
roadLanes = 3

# In[6]:


# Red signal time at which vehicles will be detected at a signal (when detection will start running)
detectionTime = 5
speedFactor = 2
speeds = {'car': 2.25*speedFactor, 'bus': 1.8*speedFactor, 'truck': 1.8*speedFactor,
          'rickshaw': 2*speedFactor, 'bike': 2.5*speedFactor,
          'ambulance': 3*speedFactor, 'fireTruck': 2*speedFactor}  # average speeds of vehicles

# speeds = {'car': 6.75, 'bus': 5.4, 'truck': 5.4,
#           'rickshaw': 6, 'bike': 7.5,
#           'ambulance': 9, 'fireTruck': 6}  # average speeds of vehicles

weatherData = {


  'Thunderstorm': 0,
  'Drizzle': 0.3,
  'Rain': 0.4,
  'Snow': 0.3,
  'Mist': 0.4,
  'Smoke': 0.2,
  'Haze': 0.3,
  'Fog': 0.2,
  'Sand': 0.1,
  'Dust': 0.1,
  'Tornado': 0,
  'clear sky': 1,
  'Few clouds': 0.8,
  'Scattered clouds': 0.7,
  'Broken clouds': 0.5,
  'overcast clouds': 0.3


}


# In[7]:


# Coordinates of start
x = {'right': [-100, -100, -100], 'down': [750, 720, 692],
     'left': [1500, 1500, 1500], 'up': [602, 630, 661]}
y = {'right': [349, 375, 400], 'down': [-100, -100, -100],
     'left': [488, 458, 430], 'up': [900, 900, 900]}


# Coordinates of signal image, timer, and vehicle count
signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]
vehicleCountCoods = [(480, 210), (880, 210), (880, 550), (480, 550)]
vehicleCountTexts = ["0", "0", "0", "0"]
trustDynamicCoords = [(30, 225), (810, 35), (1230, 555), (420, 675)]
trustHistoricCoords = [(30, 250), (810, 60), (1230, 580), (420, 700)]
trafficCongestionCoords = [(30,275),(810,85),(1120,605),(305,725)]
weatherDataCoords = [(30,300),(810,110),(1120,630),(305,750)]

# Coordinates of stop lines
stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

stops = {'right': [580, 580, 580], 'down': [320, 320, 320],
         'left': [810, 810, 810], 'up': [545, 545, 545]}

firstStep = {'right': 430, 'down': 170, 'left': 950, 'up': 695}

secondStep = {'right': 280, 'down': 20, 'left': 1100, 'up': 845}


mid = {'right': {'x': 720, 'y': 445}, 'down': {'x': 695, 'y': 460},
       'left': {'x': 680, 'y': 425}, 'up': {'x': 695, 'y': 400}}
rotationAngle = 3

# Gap between vehicles
stoppingGap = 25    # stopping gap
movingGap = 25   # moving gap


# In[8]:


vehicles = {'right': {0: [], 1: [], 2: [], 'crossed': 0}, 'down': {0: [], 1: [], 2: [], 'crossed': 0},
            'left': {0: [], 1: [], 2: [], 'crossed': 0}, 'up': {0: [], 1: [], 2: [], 'crossed': 0}}

vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'rickshaw',
                4: 'bike', 5: 'ambulance', 6: 'fireTruck'}


directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}


# In[9]:


pygame.init()
simulation = pygame.sprite.Group()


# In[10]:

class TrafficSignal:
    def __init__(self, red, yellow, green, GPIO_RED,GPIO_YELLOW, GPIO_GREEN, minimum=0, maximum=0):
        self.red = red
        self.yellow = yellow
        self.green = green
        self.minimum = minimum
        self.maximum = maximum
        self.totalGreenTime = 0
        self.GPIO_RED = GPIO_RED
        self.GPIO_YELLOW = GPIO_YELLOW
        self.GPIO_GREEN = GPIO_GREEN
        self.signalText = '---'
    

class TrustSignal:
    def __init__(self, src_lat, src_long, dest_lat, dest_long):
        self.congestion_time = ""
        self.congestion_score = 0.00
        self.weather_score = 0.00
        self.weather_description = ""
        self.hotspot_score = 0.00
        self.src_lat = src_lat
        self.src_long = src_long
        self.dest_lat = dest_lat
        self.dest_long = dest_long
        self.trust_dynamic = 0.00
        self.trust_static = 0.00

# In[11]:


class Vehicle(pygame.sprite.Sprite):

    def __init__(self, lane, vehicleClass, direction_number, direction, will_turn,active=False):
        pygame.sprite.Sprite.__init__(self)
        self.lane = lane
        self.vehicleClass = vehicleClass
        self.speed = speeds[vehicleClass]
        self.x = x[direction][lane]
        self.y = y[direction][lane]
        self.direction_number = direction_number
        self.active = active
        self.direction = direction
        self.crossed = 0
        self.willTurn = will_turn
        self.turned = 0
        self.rotateAngle = 0
        vehicles[direction][lane].append(self)
        self.index = len(vehicles[direction][lane]) - 1
        path = "/home/pi/Downloads/images/" + direction + "/" + vehicleClass + ".png"
        self.originalImage = pygame.image.load(path)
        self.currentImage = pygame.image.load(path)

        if(direction == 'right'):

            # if more than 1 vehicle in the lane of vehicle before it has crossed stop line
            if(len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0):
                self.stop = vehicles[direction][lane][self.index-1].stop - vehicles[direction][lane][self.index-1].currentImage.get_rect(
                ).width - stoppingGap         # setting stop coordinate as: stop coordinate of next vehicle - width of next vehicle - gap

            else:

                self.stop = defaultStop[direction]

            # Set new starting and stopping coordinate
            temp = self.currentImage.get_rect().width + stoppingGap
            # x[direction][lane] -= temp
            stops[direction][lane] -= temp

        elif(direction == 'left'):

            if(len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0):
                self.stop = vehicles[direction][lane][self.index-1].stop + \
                    vehicles[direction][lane][self.index -
                                              1].currentImage.get_rect().width + stoppingGap

            else:
                self.stop = defaultStop[direction]

            temp = self.currentImage.get_rect().width + stoppingGap
            # x[direction][lane] += temp
            stops[direction][lane] += temp

        elif(direction == 'down'):

            if(len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0):
                self.stop = vehicles[direction][lane][self.index-1].stop - \
                    vehicles[direction][lane][self.index -
                                              1].currentImage.get_rect().height - stoppingGap

            else:
                self.stop = defaultStop[direction]

            temp = self.currentImage.get_rect().height + stoppingGap
            # y[direction][lane] -= temp
            stops[direction][lane] -= temp

        elif(direction == 'up'):

            if(len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0):
                self.stop = vehicles[direction][lane][self.index-1].stop + \
                    vehicles[direction][lane][self.index -
                                              1].currentImage.get_rect().height + stoppingGap

            else:
                self.stop = defaultStop[direction]

            temp = self.currentImage.get_rect().height + stoppingGap
            # y[direction][lane] += temp
            stops[direction][lane] += temp

        simulation.add(self)

    def render(self, screen):
        screen.blit(self.image, (self.x, self.y))

    def move(self):

        if(self.direction == 'right'):

            # if the image has crossed stop lines
            if(self.crossed == 0 and self.x+self.currentImage.get_rect().width > stopLines[self.direction]):

                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if(self.willTurn == 1):

                if(self.lane == 0):

                    if(self.crossed == 0 or self.x+self.currentImage.get_rect().width < stopLines[self.direction] + 40):

                        if((self.x+self.currentImage.get_rect().width <= self.stop or
                            (currentGreen == 0 and currentYellow == 0) or self.crossed == 1) and
                           (self.index == 0 or self.x+self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.x += self.speed

                    else:

                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle)
                            self.x += 2.4
                            self.y -= 2.8
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or self.y-self.currentImage.get_rect().height
                               > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                               or self.x+self.currentImage.get_rect().width
                               < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)):

                                self.y -= self.speed

                elif(self.lane == 2):

                    if(self.crossed == 0 or self.x+self.currentImage.get_rect().width < mid[self.direction]['x']):

                        if((self.x+self.currentImage.get_rect().width <= self.stop or
                            (currentGreen == 0 and currentYellow == 0) or self.crossed == 1) and
                           (self.index == 0 or self.x+self.currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.x += self.speed

                    else:

                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle)
                            self.x += 2
                            self.y += 1.8
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or self.y+self.currentImage.get_rect().height
                               < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                               or self.x+self.currentImage.get_rect().width
                               < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)):

                                self.y += self.speed

            else:
                if((self.x+self.currentImage.get_rect().width <= self.stop or self.crossed == 1 or
                    (currentGreen == 0 and currentYellow == 0)) and (self.index == 0 or
                                                                     self.x+self.currentImage.get_rect().width
                                                                     < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                                                                     or (vehicles[self.direction][self.lane][self.index-1].turned == 1))):

                    # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x += self.speed  # move the vehicle

        elif(self.direction == 'down'):

            if(self.crossed == 0 and self.y+self.currentImage.get_rect().height > stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if(self.willTurn == 1):

                if(self.lane == 0):

                    if(self.crossed == 0 or self.y+self.currentImage.get_rect().height < stopLines[self.direction] + 50):

                        if((self.y+self.currentImage.get_rect().height <= self.stop
                            or (currentGreen == 1 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.y+self.currentImage.get_rect().height
                           < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.y += self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle)
                            self.x += 1.2
                            self.y += 1.8
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or
                               self.x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect(
                               ).width < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                               or self.y < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)):
                                self.x += self.speed

                elif(self.lane == 2):

                    if(self.crossed == 0 or self.y+self.currentImage.get_rect().height < mid[self.direction]['y']):

                        if((self.y+self.currentImage.get_rect().height <= self.stop
                            or (currentGreen == 1 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.y+self.currentImage.get_rect().height
                           < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.y += self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle)
                            self.x -= 2.5
                            self.y += 2
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or
                               self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect(
                               ).width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                               or self.y < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)):
                                self.x -= self.speed

            else:
                if((self.y+self.currentImage.get_rect().height <= self.stop or self.crossed == 1
                    or (currentGreen == 1 and currentYellow == 0))
                   and (self.index == 0 or self.y+self.currentImage.get_rect().height
                        < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                        or (vehicles[self.direction][self.lane][self.index-1].turned == 1))):

                    self.y += self.speed

        elif(self.direction == 'left'):

            if(self.crossed == 0 and self.x < stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if(self.willTurn == 1):

                if(self.lane == 0):

                    if(self.crossed == 0 or self.x > stopLines[self.direction] - 60):
                        if((self.x >= self.stop or (currentGreen == 2 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):
                            self.x -= self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle)
                            self.x -= 1
                            self.y += 1.2
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or
                               self.y + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect(
                               ).height < (vehicles[self.direction][self.lane][self.index-1].y - movingGap)
                               or self.x > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)):

                                self.y += self.speed

                elif(self.lane == 2):

                    if(self.crossed == 0 or self.x > mid[self.direction]['x']):
                        if((self.x >= self.stop or (currentGreen == 2 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):
                            self.x -= self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle)
                            self.x -= 1.8
                            self.y -= 2.5
                            if(self.rotateAngle == 90):
                                self.turned = 1

                        else:
                            if(self.index == 0 or
                               self.y - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect(
                               ).height > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                               or self.x > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)):

                                self.y -= self.speed

            else:
                if((self.x >= self.stop or self.crossed == 1 or (currentGreen == 2 and currentYellow == 0))
                   and (self.index == 0 or self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                        or (vehicles[self.direction][self.lane][self.index-1].turned == 1))):

                    # (if the image has not reached its stop coordinate or has crossed stop line or has green signal) and (it is either the first vehicle in that lane or it is has enough gap to the next vehicle in that lane)
                    self.x -= self.speed  # move the vehicle

        elif(self.direction == 'up'):

            if(self.crossed == 0 and self.y < stopLines[self.direction]):
                self.crossed = 1
                vehicles[self.direction]['crossed'] += 1

            if(self.willTurn == 1):

                if(self.lane == 0):

                    if(self.crossed == 0 or self.y > stopLines[self.direction] - 45):
                        if((self.y >= self.stop or (currentGreen == 3 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.y - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.y -= self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, self.rotateAngle)
                            self.x -= 2
                            self.y -= 1.5
                            if(self.rotateAngle == 90):
                                self.turned = 1
                        else:
                            if(self.index == 0 or self.x - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width > (vehicles[self.direction][self.lane][self.index-1].x + movingGap)
                               or self.y > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)):
                                self.x -= self.speed

                elif(self.lane == 2):

                    if(self.crossed == 0 or self.y > mid[self.direction]['y']):
                        if((self.y >= self.stop or (currentGreen == 3 and currentYellow == 0) or self.crossed == 1)
                           and (self.index == 0 or self.y - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                                or vehicles[self.direction][self.lane][self.index-1].turned == 1)):

                            self.y -= self.speed

                    else:
                        if(self.turned == 0):
                            self.rotateAngle += rotationAngle
                            self.currentImage = pygame.transform.rotate(
                                self.originalImage, -self.rotateAngle)
                            self.x += 1
                            self.y -= 1
                            if(self.rotateAngle == 90):
                                self.turned = 1
                        else:
                            if(self.index == 0 or self.x + vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().width < (vehicles[self.direction][self.lane][self.index-1].x - movingGap)
                               or self.y > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)):
                                self.x += self.speed
            else:
                if((self.y >= self.stop or self.crossed == 1 or (currentGreen == 3 and currentYellow == 0))
                   and (self.index == 0 or self.y - vehicles[self.direction][self.lane][self.index-1].currentImage.get_rect().height > (vehicles[self.direction][self.lane][self.index-1].y + movingGap)
                        or (vehicles[self.direction][self.lane][self.index-1].turned == 1))):

                    self.y -= self.speed


# In[12]:


# Initialization of signals with default values
def initialize():

    ts1 = TrafficSignal(0, defaultYellow, defaultMaximum,
                        13, 19, 26, defaultMinimum, defaultMaximum)
    
    signals.append(ts1)
    ts2 = TrafficSignal(ts1.red+ts1.yellow+ts1.green, defaultYellow,
                        defaultMaximum,  16, 20, 21,defaultMinimum, defaultMaximum)
    signals.append(ts2)
    ts3 = TrafficSignal(130, defaultYellow,
                        defaultMaximum,  17, 27, 22,defaultMinimum, defaultMaximum)
    signals.append(ts3)
    ts4 = TrafficSignal(195, defaultYellow,
                        defaultMaximum,  18, 23, 24,defaultMinimum, defaultMaximum)
    signals.append(ts4)

    # ts1 = TrafficSignal(0, 5, 30,13, 19, 26)
    # signals.append(ts1)
    # ts2 = TrafficSignal(35, 5, 30, 16, 20, 21)
    # signals.append(ts2)
    # ts3 = TrafficSignal(70, 5, 30, 17, 27 ,22)
    # signals.append(ts3)
    # ts4 = TrafficSignal(105, 5, 30, 18, 23, 24)
    # signals.append(ts4)


    trustSgnl1 = TrustSignal(30.730232, 76.774572, 30.733102, 76.779132)
    congestion.append(trustSgnl1)

    trustSgnl2 = TrustSignal(30.727993, 76.784416, 30.732824, 76.780174)
    congestion.append(trustSgnl2)

    trustSgnl3  = TrustSignal(30.739082, 76.774892, 30.733939, 76.779321)
    congestion.append(trustSgnl3)

    trustSgnl4 = TrustSignal(30.740305, 76.790887, 30.733919, 76.780622)
    congestion.append(trustSgnl4)


    # print("congestion array -->",congestion[0].congestion_time,congestion[0].weather_description)

    repeat()


# In[13]:


def get_vehicle_count(boxes, class_names):
    
    list_of_vehicles = ['car', 'truck', 'bus', 'motorbike', 'bicycle']
#     list_of_vehicles = ['car', 'truck', 'bus', 'motorbike', 'bicycle', 'ambulance', 'fire engine', 'auto rickshaw']
    
    total_vehicle_count = 0 # total vechiles present in the image
    dict_vehicle_count = {} # dictionary with count of each distinct vehicles detected
    
    for i in range(len(boxes)):

            class_name = class_names[i]
       
            if(class_name in list_of_vehicles):
                total_vehicle_count += 1
                dict_vehicle_count[class_name] = dict_vehicle_count.get(class_name,0) + 1
    print(total_vehicle_count, dict_vehicle_count)
    return total_vehicle_count, dict_vehicle_count

def detectVehicles():
    uuid_var = str(uuid.uuid4())
    camera.capture('/home/pi/Downloads/project/images/input/'+ uuid_var +'.jpg')
    coco_names_path = '/home/pi/Downloads/project/Assets/coco.names'
    weightsPath = '/home/pi/Downloads/project/Assets/yolov3.weights'
    configPath = '/home/pi/Downloads/project/Assets/yolov3.cfg'

    image_path = '/home/pi/Downloads/project/images/input/'+ uuid_var +'.jpg'
    video_path = '../Assets/videos/vehicles1.mp4'
    
    # load the COCO class labels our YOLO model was trained on

    Labels = []
    with open(coco_names_path,'r',encoding='utf8') as f:
        Labels = [line.strip() for line in f.readlines()]
        
        
    # initialize a list of colors to represent each possible class label
    np.random.seed(42)
    COLORS = np.random.randint(0, 255, size=(len(Labels), 3),dtype="uint8")
    
    # load our YOLO object detector trained on COCO dataset (80 classes)
    # and determine only the *output* layer names that we need from YOLO
    net = cv2.dnn.readNetFromDarknet(configPath,weightsPath)
    layers_names = net.getLayerNames()
    output_layers = [layers_names[i - 1] for i in net.getUnconnectedOutLayers()]
    
    # initialize the video stream, pointer to output video file, and
    # frame dimensions
    vs = cv2.VideoCapture(image_path)
    writer = None
    (W, H) = (None, None)
    fps=vs.get(cv2.CAP_PROP_FPS)
    
    # try to determine the total number of frames in the video file
    try:
        prop = cv2.cv.CV_CAP_PROP_FRAME_COUNT if imutils.is_cv2() \
            else cv2.CAP_PROP_FRAME_COUNT
        total = int(vs.get(prop))
        print("[INFO] {} total frames in video".format(total))

    # an error occurred while trying to determine the total
    # number of frames in the video file
    except:
        print("[INFO] could not determine # of frames in video")
        print("[INFO] no approx. completion time can be provided")
        total = -1
    
    # looping over the frames from the video file stream
    while True:
        # read the next frame from the file
        (grabbed, frame) = vs.read()

        # if the frame was not grabbed, then we have reached the end
        # of the stream
        if not grabbed:
            break

        # if the frame dimensions are empty, grab them
        if W is None or H is None:
            (H, W) = frame.shape[:2]

        # construct a blob from the input frame and then perform a forward
        # pass of the YOLO object detector, giving us our bounding boxes
        # and associated probabilities
        blob = cv2.dnn.blobFromImage(frame, 1 / 255.0, (416, 416),swapRB=True, crop=False)
        net.setInput(blob)
        start = time.time()
        layerOutputs = net.forward(output_layers)
        end = time.time()

        # initialize our lists of detected bounding boxes, confidences,
        # and class IDs, respectively
        boxes = []
        confidences = []
        classIDs = []
        classname = []
    # print(layerOutputs)
        # loop over each of the layer outputs
        for output in layerOutputs:
            # loop over each of the detections
            for detection in output:
                # extract the class ID and confidence (i.e., probability)
                # of the current object detection

    # print(detection)
                scores = detection[5:]
                classID = np.argmax(scores)
                confidence = scores[classID]

                # filter out weak predictions by ensuring the detected
                # probability is greater than the minimum probability
                if confidence > 0.5:
                    # scale the bounding box coordinates back relative to
                    # the size of the image, keeping in mind that YOLO
                    # actually returns the center (x, y)-coordinates of
                    # the bounding box followed by the boxes' width and
                    # height
                    box = detection[0:4] * np.array([W, H, W, H])
                    (centerX, centerY, width, height) = box.astype("int")

                    # use the center (x, y)-coordinates to derive the top
                    # and and left corner of the bounding box
                    x = int(centerX - (width / 2))
                    y = int(centerY - (height / 2))

                    # update our list of bounding box coordinates,
                    # confidences, and class IDs
                    boxes.append([x, y, int(width), int(height)])
                    confidences.append(float(confidence))
                    classIDs.append(classID)
                    classname.append(Labels[classID])

        # apply non-maxima suppression to suppress weak, overlapping
        # bounding boxes
        idxs = cv2.dnn.NMSBoxes(boxes, confidences, 0.5,0.5)


        # ensure at least one detection exists
        if len(idxs) > 0:
            # loop over the indexes we are keeping
            for i in idxs.flatten():
                # extract the bounding box coordinates
                (x, y) = (boxes[i][0], boxes[i][1])
                (w, h) = (boxes[i][2], boxes[i][3])

                # draw a bounding box rectangle and label on the frame
                color = [int(c) for c in COLORS[classIDs[i]]]

                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)

                text = "{}: {:.4f}".format(Labels[classIDs[i]],confidences[i])

                cv2.putText(frame, text, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

        # cv2.imshow("frame",frame)
        # cv2.waitKey(0)
        # check if the video writer is None
#         print("idxs --> ",idxs)
#         print("init boxes-->",boxes)
#         print("init names-->",classname)

        boxes = [boxes[i] for i in idxs]
        classname = [classname[i] for i in idxs]

    #     print("final boxes -->",boxes)
    #     print("final names -->",classname)
        total_vehicles, each_vehicle = get_vehicle_count(boxes, classname)
        # print("Total vehicles in image", total_vehicles)
        # print("Each vehicles count in image", each_vehicle)
        if writer is None:
            # initialize our video writer
            fourcc = cv2.VideoWriter_fourcc(*"MJPG")
            writer = cv2.VideoWriter('/home/pi/Downloads/project/images/output/predictedResult.jpeg', fourcc, 20,
                (frame.shape[1], frame.shape[0]), True)

            # some information on processing single frame
            if total > 0:
                elap = (end - start)
                print("[INFO] single frame took {:.4f} seconds".format(elap))
                print("[INFO] estimated total time to finish: {:.4f}".format(
                    elap * total))

        # write the output frame to disk
        writer.write(frame)

    # release the file pointers
    # print("[INFO] cleaning up...")
    # writer.release()
    # vs.release()
    
    # car=each_vehicle.get('car',0)
    # motorbike=each_vehicle.get('motorbike',0)
    # bicycle=each_vehicle.get('bicycle',0)
    # bus=each_vehicle.get('bus',0)
    # truck=each_vehicle.get('truck',0)
    
    
    # print(car,motorbike,bicycle,bus,truck)
    return each_vehicle
    
    

def setTime():

    global noOfCars, noOfBikes, noOfBuses, noOfTrucks, noOfRickshaws, noOfAmbulances, noOffireTrucks, noOfPoliceCars, noOfLanes
    global carTime, busTime, truckTime, rickshawTime, bikeTime

    noOfCars, noOfBuses, noOfTrucks, noOfRickshaws, noOfBikes, noOfAmbulances, noOffireTrucks, noOfPoliceCars = 0, 0, 0, 0, 0, 0, 0, 0

    # vehicle_dict = detectVehicles()

    # for key,value in vehicle_dict.items():

    #     if(key == 'car'):
    #         noOfCars += value
    #     elif(key == 'bus'):
    #         noOfBuses += value
    #     elif(key == 'truck'):
    #         noOfTrucks += value
    #     elif(key == 'motorbike'):
    #         noOfBikes += value
        
    for i in range(0, roadLanes):

        for j in range(len(vehicles[directionNumbers[nextGreen]][i])):

            vehicle = vehicles[directionNumbers[nextGreen]][i][j]

            if(vehicle.crossed == 0):
                vclass = vehicle.vehicleClass
 
                if(vclass == 'car'):
                    noOfCars += 1
                elif(vclass == 'bus'):
                    noOfBuses += 1
                elif(vclass == 'truck'):
                    noOfTrucks += 1
                elif(vclass == 'motorbike'):
                    noOfBikes += 1
                elif(vclass == 'rickshaw'):
                    noOfRickshaws += 1
                elif(vclass == 'ambulance'):
                    noOfAmbulances += 1
                elif(vclass == 'fireTruck'):
                    noOffireTrucks += 1
                


#     print("For Vehicles Going = ",directionNumbers[(currentGreen+1)%noOfSignals])
#     print("Cars = ",noOfCars)
#     print("Autos = ",noOfRickshaws)
#     print("Buses = ",noOfBuses)
#     print("Trucks = ",noOfTrucks)
#     print("Bikes = ",noOfBikes)

    # total_vehicles = noOfCars + noOfRickshaws + noOfBuses + noOfTrucks + noOfBikes

    greenTime = math.ceil(((noOfCars*carTime) + (noOfRickshaws*rickshawTime) + (noOfBuses*busTime) + (noOfTrucks*truckTime) + (
        noOfBikes*bikeTime) + (noOfAmbulances*ambulanceTime) + (noOffireTrucks*fireTruckTime) + (noOfPoliceCars*policeCarTime))/(noOfLanes+1))

    print('Green Time: ', greenTime)
    if(greenTime < defaultMinimum):
        greenTime = defaultMinimum
    elif(greenTime > defaultMaximum):
        greenTime = defaultMaximum

    signals[(nextGreen) % (noOfSignals)].green = greenTime
    buffer = defaultMaximum - greenTime

    signals[(nextGreen + 1) % (noOfSignals)].red -= buffer
    signals[(nextGreen + 2) % (noOfSignals)].red -= buffer



# In[14]:

def updateValuesAfterSkip():

    buffer = signals[nextGreen].red - \
        (defaultMinimum + defaultYellow)
    signals[currentGreen].green -= buffer
    signals[nextGreen].red -= buffer
    signals[(nextGreen + 1) % (noOfSignals)].red -= buffer
    signals[(nextGreen + 2) % (noOfSignals)].red -= buffer
    # print("skipping time of direction ==>",
    #       directionNumbers[currentGreen])


def skipTimer():
    
    global displaySkip

    # if green of current is greater than 10 then definitely red of next will be greater than 15
    while True:

        # print("skip")
        if(Emergency == False and signals[currentGreen].green > 10):

            totalVehicles = []
            for i in range(roadLanes):
                totalVehicles.extend(vehicles[directionNumbers[currentGreen]][i])

            lanes = vehicles[directionNumbers[currentGreen]]
            
            displaySkip = False
            skip = True
            if(len(totalVehicles) == lanes['crossed']):
                updateValuesAfterSkip()
                print("skipping time due to no vehicle")

            else:
                for j in range(len(totalVehicles)):
                    vehicle = totalVehicles[j]
                    WIDTH, HEIGHT = pygame.display.get_surface().get_size()
                    if(vehicle.crossed == 0 and (vehicle.x > 0 and vehicle.x < WIDTH) and (vehicle.y > 0 and vehicle.y < HEIGHT)):

                        if((directionNumbers[currentGreen] == 'right' and
                            vehicle.x + vehicle.currentImage.get_rect().width > firstStep[directionNumbers[currentGreen]]) or
                        (directionNumbers[currentGreen] == 'down' and
                            vehicle.y + vehicle.currentImage.get_rect().height > firstStep[directionNumbers[currentGreen]]) or
                            (directionNumbers[currentGreen] == 'left' and
                            vehicle.x < firstStep[directionNumbers[currentGreen]]) or
                                (directionNumbers[currentGreen] == 'up' and
                                vehicle.y < firstStep[directionNumbers[currentGreen]])):
                            skip = False
                            break

                if skip:
                    # print("vehicle ==>", vehicle.x, " ", vehicle.y)
                    updateValuesAfterSkip()
                    # print("vehicle = ", j)
            
            displaySkip = skip
            time.sleep(1)
            displaySkip = False
        time.sleep(5)


def distanceTimeAssignment():

    # time assignment for 20m as 10sec, 40m as 15sec and for longer distances using yolo
    if(directionNumbers[nextGreen] == 'right' or directionNumbers[nextGreen] == 'down'):

        direction = directionNumbers[nextGreen]
        if(firstStep[direction] < stops[direction][0] and firstStep[direction] < stops[direction][1] and firstStep[direction] < stops[direction][2]):
            signals[nextGreen].green = defaultMinimum
            print("less than 20m")

        elif(secondStep[direction] < stops[direction][0] and secondStep[direction] < stops[direction][1] and secondStep[direction] < stops[direction][2]):
            signals[nextGreen].green = defaultMinimum + 5
            print("less than 40m")

        else:
            setTime()
            print("using yolo")


    elif(directionNumbers[nextGreen] == 'left' or directionNumbers[nextGreen] == 'up'):

        direction = directionNumbers[nextGreen]
        if(firstStep[direction] > stops[direction][0] and firstStep[direction] > stops[direction][1] and firstStep[direction] > stops[direction][2]):
            signals[nextGreen].green = defaultMinimum
            print("less than 20m")

        elif(secondStep[direction] > stops[direction][0] and secondStep[direction] > stops[direction][1] and secondStep[direction] > stops[direction][2]):
            signals[nextGreen].green = defaultMinimum + 5
            print("less than 40m")

        else:
            setTime()
            print("using yolo")



def repeat():
    
    global currentGreen, currentYellow, nextGreen

    # skipTime = 5
    while(signals[currentGreen].green > 0):

        if(len(activePriorityVehicles) == 1):
            HandlePriorityVehicle(activePriorityVehicles[0])
            break
            

        printStatus()
        updateValues()

        # set time of next green signal
        if(signals[nextGreen % noOfSignals].red == detectionTime):
                setTime()
                # print("using yolo")
                #distanceTimeAssignment()
                

        time.sleep(1)

        
        
        
    currentYellow = 1   # set yellow signal on
    for i in range(0, roadLanes):
        # for all the lanes with current yellow signal
        stops[directionNumbers[currentGreen]
            ][i] = defaultStop[directionNumbers[currentGreen]]
        for vehicle in vehicles[directionNumbers[currentGreen]][i]:
            vehicle.stop = defaultStop[directionNumbers[currentGreen]]

    # while the timer of current yellow signal is not zero
    while(signals[currentGreen].yellow > 0):
        
        if(len(activePriorityVehicles) == 1):
            HandlePriorityVehicle(activePriorityVehicles[0])
            break

        printStatus()
        updateValues()
        time.sleep(1)

    currentYellow = 0   # set yellow signal off

       
    signals[currentGreen].green = defaultMaximum
    signals[currentGreen].yellow = defaultYellow
    signals[currentGreen].red = defaultRed

    currentGreen = nextGreen  # set next signal as green signal
    nextGreen = (currentGreen+1) % noOfSignals    # set next green signal

    # set the red time of next to next signal as (yellow time + green time) of next signal
    temp = signals[nextGreen].red
    signals[nextGreen].red = signals[currentGreen].yellow + \
        signals[currentGreen].green

    # checking if the current red timer exceeds the previous ongoing timer or not
    if(signals[nextGreen].red > temp):
        print("I will go crazy...!")
    
    repeat()



def findActivePriorityVehicles():
    
    global Emergency,activePriorityVehicles
    while(True):
        priorityVehicleList = []

        for i in range(0, noOfSignals):
                for j in range(0, roadLanes):
                    for k in range(len(vehicles[directionNumbers[i]][j])):
                        vehicle = vehicles[directionNumbers[i]][j][k]
                        vclass = vehicle.vehicleClass
                        if(vehicle.crossed == 0 and (vclass == "ambulance") and vehicle.active == True):
                            priorityVehicleList.append(vehicle)
        
        activePriorityVehicles = priorityVehicleList
        
        print("Active List Length -> ",len(activePriorityVehicles))     
        
        if(len(activePriorityVehicles) == 1):
            Emergency = True
            print("Handling Vehicle at -->",activePriorityVehicles[0].direction_number)
            
        time.sleep(1)




def priorityVehicleDetection(vehicle):
    
    # detecting using YOLO if the image contains 
    # a priority vehicle or not
    print("Vehicle at point -->",(vehicle.x,vehicle.y))

    # WIDTH, HEIGHT = pygame.display.get_surface().get_size()
    if(vehicle.crossed == 0):
        if((directionNumbers[currentGreen] == 'right' and
            vehicle.x + vehicle.currentImage.get_rect().width < firstStep[directionNumbers[currentGreen]]) or
            (directionNumbers[currentGreen] == 'down' and
            vehicle.y + vehicle.currentImage.get_rect().height < firstStep[directionNumbers[currentGreen]]) or
            (directionNumbers[currentGreen] == 'left' and
            vehicle.x > firstStep[directionNumbers[currentGreen]]) or
            (directionNumbers[currentGreen] == 'up' and
            vehicle.y > firstStep[directionNumbers[currentGreen]])):

            # Priority vehicle is at a distance of more than 20m 
            return True
    
    return False


def HandlePriorityVehicle(vehicle):
    
    global currentGreen, Emergency, currentYellow, nextGreen
    
    if(currentGreen == vehicle.direction_number):
        
        if(signals[currentGreen].green == 0 and signals[currentGreen].yellow > 0):
            
            # PV at a yellow signal 
            print(f"---------------------Handling at light Yellow {vehicle.direction_number}-----------------------")
            currentYellow = 0
            bufferTime = defaultYellow
            signals[currentGreen].green = defaultMinimum + bufferTime

            while(signals[currentGreen].green > 0):
                
                printStatus()
                if(bufferTime == 0):

                    if(priorityVehicleDetection(vehicle) == True):    
                        bufferTime = defaultYellow
                        signals[currentGreen].green += bufferTime
                        
                    else:
                        
                        break
                else:
                   
                    bufferTime -= 1
                    signals[currentGreen].green -= 1
                
                time.sleep(1)
            
            Emergency = False
            signals[nextGreen % noOfSignals].red = signals[currentGreen].green + signals[currentGreen].yellow
            signals[(nextGreen + 1) % (noOfSignals)].red = defaultMaximum + defaultYellow + signals[nextGreen % noOfSignals].red
            signals[(nextGreen + 2) % (noOfSignals)].red = defaultMaximum + defaultYellow + signals[(nextGreen + 1) % (noOfSignals)].red
            repeat()
            

        else:
            
            # PV at a green signal
            print(f"-------------------------Handling at light Green {vehicle.direction_number}--------------------------")
            while(signals[currentGreen].green > defaultMinimum):
                printStatus()
                updateValues()
                time.sleep(1)
            

            if priorityVehicleDetection(vehicle):

                bufferTime = defaultYellow
                signals[currentGreen].green  = defaultMinimum + bufferTime
            
                while(signals[currentGreen].green > 0):

                    printStatus()
                    if(bufferTime == 0):

                        if(priorityVehicleDetection(vehicle) == True):    
                            bufferTime = defaultYellow
                            signals[currentGreen].green += bufferTime
                        else:
                            # green signal is 10 and PV is not detected
                            break
                    else:
                        bufferTime -= 1
                        signals[currentGreen].green -= 1
                    
                    time.sleep(1)
                
                Emergency = False
                signals[nextGreen % noOfSignals].red = signals[currentGreen].green + signals[currentGreen].yellow
                signals[(nextGreen + 1) % (noOfSignals)].red = defaultMaximum + defaultYellow + signals[nextGreen % noOfSignals].red
                signals[(nextGreen + 2) % (noOfSignals)].red = defaultMaximum + defaultYellow + signals[(nextGreen + 1) % (noOfSignals)].red
                
                repeat()

            else:
                Emergency = False
                repeat()

            
        
        
    elif(nextGreen == vehicle.direction_number):

        print(f"-------------------------Handling at Next Green {vehicle.direction_number} -----------------------")

        if(signals[currentGreen].green> defaultMinimum):
            signals[currentGreen].green = defaultMinimum
            
        signals[nextGreen % noOfSignals].red = signals[currentGreen].green + signals[currentGreen].yellow

        while(signals[currentGreen].green > 0):
            printStatus()
            signals[currentGreen].green -= 1
            signals[nextGreen % noOfSignals].red -= 1
            time.sleep(1)
        
        currentYellow = 1  # set yellow signal on
        for i in range(0, roadLanes):
            # for all the lanes with current yellow signal
            stops[directionNumbers[currentGreen]
                ][i] = defaultStop[directionNumbers[currentGreen]]
            for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                vehicle.stop = defaultStop[directionNumbers[currentGreen]]

        
        while(signals[currentGreen].yellow > 0):
            printStatus()
            signals[currentGreen].yellow -= 1
            signals[nextGreen % noOfSignals].red -= 1
            time.sleep(1)
        currentYellow = 0   # set yellow signal off
        

        signals[currentGreen].green = defaultMaximum
        signals[currentGreen].yellow = defaultYellow
        signals[currentGreen].red = defaultRed

        signals[nextGreen % noOfSignals].red = defaultRed

        currentGreen = nextGreen
        nextGreen = (currentGreen + 1)%noOfSignals
        bufferTime = defaultYellow
        signals[currentGreen].green = defaultMinimum + bufferTime

        while(signals[currentGreen].green > 0):
            
            printStatus()
            if(bufferTime == 0):
                if(priorityVehicleDetection(vehicle) == True):    
                    bufferTime = defaultYellow
                    signals[currentGreen].green += bufferTime
                else:
                    # green signal is 10 and PV is not detected
                    break
                   
            else:
                bufferTime -= 1
                signals[currentGreen].green -= 1
            
            time.sleep(1)
        
        Emergency = False
        signals[nextGreen % noOfSignals].red = signals[currentGreen].green + signals[currentGreen].yellow
        signals[(nextGreen + 1) % (noOfSignals)].red = defaultMaximum + defaultYellow + signals[nextGreen % noOfSignals].red
        signals[(nextGreen + 2) % (noOfSignals)].red = defaultMaximum + defaultYellow + signals[(nextGreen + 1) % (noOfSignals)].red
        
        repeat()


    # PV at a red signal
    else:
        
        print(f"-------------------------Handling at light Red {vehicle.direction_number} ---------------------------")
        prioritySignal = vehicle.direction_number
        

        if(signals[currentGreen].green> defaultMinimum):
            signals[currentGreen].green = defaultMinimum
        
        signals[prioritySignal].red = signals[currentGreen].green + signals[currentGreen].yellow

        while(signals[currentGreen].green > 0):
            printStatus()
            signals[currentGreen].green -= 1
            signals[prioritySignal].red -= 1
            time.sleep(1)
        
        currentYellow = 1  # set yellow signal on
        for i in range(0, roadLanes):
            # for all the lanes with current yellow signal
            stops[directionNumbers[currentGreen]
                ][i] = defaultStop[directionNumbers[currentGreen]]
            for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                vehicle.stop = defaultStop[directionNumbers[currentGreen]]

        
        while(signals[currentGreen].yellow > 0):
            printStatus()
            signals[currentGreen].yellow -= 1
            signals[prioritySignal].red -= 1
            time.sleep(1)
        currentYellow = 0   # set yellow signal off

        signals[currentGreen].green = defaultMaximum
        signals[currentGreen].yellow = defaultYellow
        signals[currentGreen].red = defaultRed

       
        currentGreen = prioritySignal
        bufferTime = defaultYellow
        signals[prioritySignal].green = defaultMinimum + bufferTime

        while(signals[prioritySignal].green > 0):
            
            printStatus()
            if(bufferTime == 0):
                if(priorityVehicleDetection(vehicle) == True):    
                    bufferTime = defaultYellow
                    signals[prioritySignal].green += bufferTime
                    
                else:
                    # green signal is 10 and PV is not detected
                    break
                  
            else:
                bufferTime -= 1
                signals[prioritySignal].green -= 1
            time.sleep(1)
        
        
        Emergency = False
        signals[nextGreen % noOfSignals].red = signals[prioritySignal].green + signals[prioritySignal].yellow
        signals[(nextGreen + 1) % (noOfSignals)].red = defaultMaximum + defaultYellow + signals[nextGreen % noOfSignals].red
        signals[(nextGreen + 2) % (noOfSignals)].red = defaultMaximum + defaultYellow + signals[(nextGreen + 1) % (noOfSignals)].red

        while(signals[prioritySignal].green > 0):
            printStatus()
            signals[prioritySignal].green -= 1
            signals[nextGreen % noOfSignals].red -= 1
            time.sleep(1)
        
        setTime()

        currentYellow = 1
        while(signals[prioritySignal].yellow > 0):
            printStatus()
            signals[prioritySignal].yellow -= 1
            signals[(nextGreen) % (noOfSignals)].red -= 1
            time.sleep(1)
        currentYellow = 0

        signals[prioritySignal].green = defaultMaximum
        signals[prioritySignal].yellow = defaultYellow

        currentGreen = nextGreen
        nextGreen = (currentGreen + 1)%noOfSignals
        signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green

        
        repeat()
        
        



# In[15]:

# Print the signal timers on cmd
def printStatus():
    

    print("Current Green -->",currentGreen)
    print("Next Green -->", nextGreen)
    for i in range(0, noOfSignals):
        if(i == currentGreen):
            if(currentYellow == 0):
                print(" GREEN TS", i+1, "-> r:",
                      signals[i].red, " y:", signals[i].yellow, " g:", signals[i].green)
            else:
                print("YELLOW TS", i+1, "-> r:",
                      signals[i].red, " y:", signals[i].yellow, " g:", signals[i].green)
        else:
            print("   RED TS", i+1, "-> r:",
                  signals[i].red, " y:", signals[i].yellow, " g:", signals[i].green)
    print()


# In[16]:


# Update values of the signal timers after every second

def updateValues():
    
    # print("update values Emergency -->",Emergency)
    
    for i in range(0, noOfSignals):
        if(i == currentGreen):
            if not currentYellow:
                signals[i].green -= 1
                signals[i].totalGreenTime += 1
            else:
                signals[i].yellow -= 1
        else:
            signals[i].red -= 1


# In[17]:

def calculatetrustDynamic():

    global hotspot_region
    # total = 0
    # totalCrossed = 0
    # for i in range(0, noOfSignals):

    #     for j in range(0, roadLanes):

    #         total += len(vehicles[directionNumbers[i]][j])

    #     total -= vehicles[directionNumbers[i]]['crossed']
        # totalCrossed += vehicles[directionNumbers[i]]['crossed']

    # if(total != 0):
    for i in range(0, noOfSignals):
        vehicleOnOneSide = 0
        for j in range(0, roadLanes):

            for k in range(len(vehicles[directionNumbers[i]][j])):
                vehicle = vehicles[directionNumbers[i]][j][k]
                if(vehicle.crossed == 0):
                    vehicleOnOneSide += 1

        # print("Vehicle on one side = ", vehicleOnOneSide)

        # trust score defined per 100 vehicles
        x = vehicleOnOneSide
        val = math.exp(-0.03 * x)
        congestion[i].hotspot_score = round(val*weightage,2)
        # print("Pygame vehicles = ",round(valweightage,2))
        congestion[i].trust_dynamic = round(congestion[i].congestion_score + congestion[i].weather_score + congestion[i].hotspot_score,2)

        # print("hotspot = ",hotspot_region)
        if hotspot_region:
            congestion[i].trust_dynamic = round(congestion[i].trust_dynamic*weightage,2)


def directionNumberFromDistribution():

    global distribution

    distribution = [250, 500, 750, 1000]

    # deciding the direction_number from
    # a range of values from 1 to 1000
    temp = random.randint(0, 999)
    direction_number = 0
    calculatetrustDynamic()
    if(temp < distribution[0]):
        direction_number = 0
    elif(temp < distribution[1]):
        direction_number = 1
    elif(temp < distribution[2]):
        direction_number = 2
    elif(temp < distribution[3]):
        direction_number = 3

    return direction_number


def directionNumberFromtrustDynamicScores():

    calculatetrustDynamic()

    # distribution = [
    #     int(trust[0].dynamic*250), int((trust[0].dynamic+trust[1].dynamic) *
    #                            250), int((trust[0].dynamic+trust[1].dynamic+trust[2].dynamic) *
    #                                      250), int((trust[0].dynamic+trust[1].dynamic+trust[2].dynamic+trust1[3])*250)
    # ]
    trustDynamic = []
    for i in range(0,noOfSignals):
        trustDynamic.append(congestion[i].trust_dynamic)

    max_item = max(trustDynamic)
    return trustDynamic.index(max_item)


# In[18]:


def congestionInfo():
    

    while(True):

        for i in range(0,noOfSignals):
            
            s_lat = congestion[i].src_lat
            s_long = congestion[i].src_long
            d_lat = congestion[i].dest_lat
            d_long = congestion[i].dest_long

            # Define the API endpoint for traffic data
            url = f"https://maps.googleapis.com/maps/api/distancematrix/json?origins={s_lat}%2C{s_long}&destinations={d_lat}%2C{d_long}&mode=driving&departure_time=now&traffic_model=best_guess&key={GOOGLE_API_KEY}&alternatives=true"

            # Make a request to the API endpoint
            response = requests.get(url)

            # Decode the JSON response
            data = response.json()

            # Get the traffic congestion status

            status = data['rows'][0]['elements'][0]['status']

            # Check the status and display the traffic congestion status
            if status == "OK":
                congestionTime = data['rows'][0]['elements'][0]['duration_in_traffic']['text']
                # print("Traffic congestion: ", congestionTime)
                congestion[i].congestion_time = congestionTime
                # print(re.findall(r'\d+', congestionTime))  '3 min'
                minutes = int(re.findall(r'\d+', congestionTime)[0])
                scaled_time = minutes/60  # 0 to 1
                congestion[i].congestion_score = round((1.00 - scaled_time)*weightage,2)
                # print("Google congestion = ",round((1.00 - scaled_time)weightage,2))
                # congestion[i].trust_dynamic += round((1.00 - scaled_time)*weightage,2)
            else:
                print("Error: Traffic information is not available for this location.")


            # Define the API endpoint for weather data
            url2 = f"https://api.openweathermap.org/data/2.5/weather?lat={d_lat}&lon={d_long}&appid={OPEN_WEATHER_API_KEY}"

            # Make a request to the API endpoint
            response2 = requests.get(url2)

            # Decode the JSON response
            data2 = response2.json()
            description = data2['weather'][0]['description']
            for key in weatherData:
                if description in key:
                    congestion[i].weather_score = round((weatherData[description])*weightage,2)
                    # print("Weather Api = ",round((weatherData[description])weightage,2))
                    # congestion[i].trust_dynamic += round((weatherData[description])*weightage,2)
                    break

            congestion[i].weather_description = description

        time.sleep(60)



def simulationTime():

    global timeElapsed, simTime
    while(True):

        timeElapsed += 1
        time.sleep(1)
        if(timeElapsed == simTime):
            totalVehicles = 0
            print('Lane-wise Vehicle Counts')

            # data.append(distribution[0]/1000)
            # data.append((distribution[1] - distribution[0])/1000)
            # data.append((distribution[2] - distribution[1])/1000)
            # data.append((distribution[3] - distribution[2])/1000)

            for i in range(noOfSignals):
                print('Lane', i+1, ':',
                      vehicles[directionNumbers[i]]['crossed'])
                data.append(vehicles[directionNumbers[i]]['crossed'])
                totalVehicles += vehicles[directionNumbers[i]]['crossed']

            # data.append(totalVehicles)
            # with open('../data/4.11-Way-Analysis-Dynamic.csv', 'a', newline='') as f:
            #     writer = csv.writer(f)
            #     writer.writerow(data)

            trustScoreData.append(distribution[0]/1000)
            trustScoreData.append((distribution[1] - distribution[0])/1000)
            trustScoreData.append((distribution[2] - distribution[1])/1000)
            trustScoreData.append((distribution[3] - distribution[2])/1000)

            for i in range(noOfSignals):

                vehicleCrossedOnOneSide = vehicles[directionNumbers[i]]['crossed']
                value = round(vehicleCrossedOnOneSide/totalVehicles, 2)
                trustScoreData.append(value)

            # with open('./trustScore.csv', 'a', newline='') as f:
            #     writer = csv.writer(f)
            #     writer.writerow(trustScoreData)

            print('Total vehicles passed: ', totalVehicles)
            print('Total time passed: ', timeElapsed)

            os._exit(1)


def generateVehicles():

    while(True):

        vehicle_type = random.randint(0, 4)
        
        # if(vehicle_type == 5):
        #     vehicle_type = random.randint(0,4)


        # if(timeElapsed % 30 == 0):
        #     vehicle_type = 5
        
        lane_number = random.randint(0, 2)

        will_turn = 0

        # deciding whether the vehicle will turn or not
        if(lane_number == 2 or lane_number == 0):
            temp = random.randint(0, 5)
            if(temp < 3):
                will_turn = 1
            elif(temp < 6):
                will_turn = 0

        # using the fixed distribution to distribute vehicles in simulation
        direction_number = directionNumberFromDistribution()

        # using variable distribution to distribute vehicles in simulation
        # direction_number = directionNumberFromtrust1Scores()

        # print(direction_number)
        Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number,
                directionNumbers[direction_number], will_turn, (vehicle_type == 5))

        time.sleep(1)


def trustScoreDataCollection():
    '''
    Initialising the csv file for trust score collection
    '''
    header = ['P1', 'P2', 'P3', 'P4', 'TrustLane1',
              'TrustLane2', 'TrustLane3', 'TrustLane4']
    # with open('./trustScore.csv', 'w', encoding='UTF8', newline='') as f:
    #     writer = csv.writer(f)
    #     # write the header
    #     writer.writerow(header)

    '''
    Reading possible trust scores already available
    '''
    with open('./trustScore.csv', 'r') as csvfile:
        csv_dict = [row for row in csv.DictReader(csvfile)]
        if len(csv_dict) == 0:
            print('csv file is empty')
        else:
            trustScoreDict = csv_dict[-1]
            idx = 0
            for value in list(trustScoreDict.values())[4:]:
                congestion[idx].trust_historic = float(value)
                idx += 1

            # In[ ]:

class Checkbox:
    def __init__(self, x, y, text, font, color):
        self.rect = pygame.Rect(x, y, 20, 20)
        self.checked = False
        self.text = font.render(text, True, color)

    def draw(self, surface):
        GRAY = (128, 128, 128)
        RED = (255, 0, 0)
        pygame.draw.rect(surface, GRAY, self.rect, 2)
        if self.checked:
            pygame.draw.rect(surface, RED, self.rect.inflate(-6, -6))
        surface.blit(self.text, (self.rect.right + 10, self.rect.centery - 10))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.checked = not self.checked


def Main():
    
    global hotspot_region
    thread1 = threading.Thread(
        name="simulationTime", target=simulationTime, args=())
    # thread1.daemon = True
    thread1.start()

    
    thread2 = threading.Thread(
        name="initialization", target=initialize, args=())    # initialization
    # thread2.daemon = True
    thread2.start()
    
   
    # Colours
    black = (0, 0, 0)
    white = (255, 255, 255)
    red = (255,0,0)
    green = (0,255,0)
    yellow = (255,255,0)

    # Screensize
    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)

    # Setting background image i.e. image of intersection
    background = pygame.image.load(
        '/home/pi/Downloads/images/intersection/intersection-4-Way.png')

    screen = pygame.display.set_mode(screenSize, pygame.RESIZABLE)
    pygame.display.set_caption("TRAFFIC SIMULATION")

    icon = pygame.image.load('/home/pi/Downloads/images/Icons/rush.png')
    pygame.display.set_icon(icon)

    # Loading signal images and font
    redSignal = pygame.image.load('/home/pi/Downloads/images/signals/red.png')
    yellowSignal = pygame.image.load('/home/pi/Downloads/images/signals/yellow.png')
    greenSignal = pygame.image.load('/home/pi/Downloads/images/signals/green.png')
    font = pygame.font.Font(None, 30)

    thread3 = threading.Thread(
        name="generateVehicles", target=generateVehicles, args=())    # Generating vehicles
    # thread3.daemon = True
    thread3.start()

    # thread4 = threading.Thread(
    #     name="findPriorityVehicles", target=findActivePriorityVehicles,args=())
    # # thread4.daemon = True
    # thread4.start()

    thread5 = threading.Thread(
    name="skipTimer", target=skipTimer, args=())
    # thread5.daemon = True
    thread5.start()
        
    # trustScoreDataCollection()

    thread6 = threading.Thread(
    name="congestion", target=congestionInfo, args=())
    # thread6.daemon = True
    thread6.start()

    FPS = 60
    clock = pygame.time.Clock()
    # Create a checkbox
    checkbox = Checkbox(25, 25, "HOTSPOT", font, black)

    while True:
        
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            elif event.type == pygame.MOUSEBUTTONDOWN:
                checkbox.handle_event(event)
                hotspot_region = checkbox.checked

        screen.blit(background, (0, 0))

        # Draw checkbox
        checkbox.draw(screen)

        # display signal and set timer according to current status: green, yellow, or red
        
        for i in range(0, noOfSignals):
            if(i == currentGreen):
                if(currentYellow == 1):
                    # if Emergency:
                    #     signals[i].signalText = "EMGY"
                    # else:
                    # Current signal is yellow
                    if(signals[i].yellow == 0):
                        
                        GPIO.output(signals[i].GPIO_RED,GPIO.HIGH)
                        GPIO.output(signals[i].GPIO_YELLOW,GPIO.LOW)
                        GPIO.output(signals[i].GPIO_GREEN,GPIO.LOW)
                        # time.sleep(0.09)
                        # GPIO.output(18,GPIO.LOW)
                        # time.sleep(0.09)
                        signals[i].signalText = 'STOP'
                    else:
                        signals[i].signalText = signals[i].yellow
                        GPIO.output(signals[i].GPIO_RED,GPIO.LOW)
                        GPIO.output(signals[i].GPIO_YELLOW,GPIO.HIGH)
                        GPIO.output(signals[i].GPIO_GREEN,GPIO.LOW)
                        # time.sleep(0.09)
                        # GPIO.output(17,GPIO.LOW)
                        # time.sleep(0.09)
                    screen.blit(yellowSignal,signalCoods[i])
                    
                else:
                    # if Emergency:
                    #     signals[i].signalText = "EMGY"
                    # else:
                        # Current signal is green
                    if(signals[i].green == 0):
                        signals[i].signalText = "SLOW"
                        GPIO.output(signals[i].GPIO_RED,GPIO.LOW)
                        GPIO.output(signals[i].GPIO_YELLOW,GPIO.HIGH)
                        GPIO.output(signals[i].GPIO_GREEN,GPIO.LOW)
                        # time.sleep(0.09)
                        # GPIO.output(17,GPIO.LOW)
                        # time.sleep(0.09)
                    else:
                        GPIO.output(signals[i].GPIO_RED,GPIO.LOW)
                        GPIO.output(signals[i].GPIO_YELLOW,GPIO.LOW)
                        GPIO.output(signals[i].GPIO_GREEN,GPIO.HIGH)
                        # time.sleep(0.09)
                        # GPIO.output(23,GPIO.LOW)
                        # time.sleep(0.09)
                        if displaySkip:
                            signals[i].signalText = "SKIP"
                        else:
                            signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])

            else:
                # if Emergency:
                #     signals[i].signalText = "EMGY"
                # else:
                    # Iterating on a red signal
                    # if(signals[i].red <= 15):
                if(signals[i].red == 0):
                    signals[i].signalText = "GO"

                    GPIO.output(signals[i].GPIO_RED,GPIO.LOW)
                    GPIO.output(signals[i].GPIO_YELLOW,GPIO.LOW)
                    GPIO.output(signals[i].GPIO_GREEN,GPIO.HIGH)
                    # time.sleep(0.09)
                    # GPIO.output(23,GPIO.LOW)
                    # time.sleep(0.09)
                else:
                    
                    GPIO.output(signals[i].GPIO_RED,GPIO.HIGH)
                    GPIO.output(signals[i].GPIO_YELLOW,GPIO.LOW)
                    GPIO.output(signals[i].GPIO_GREEN,GPIO.LOW)
                    # time.sleep(0.09)
                    # GPIO.output(18,GPIO.LOW)
                    # time.sleep(0.09)
                    signals[i].signalText = signals[i].red
                    # else:
                    #     signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])

        signalTexts = ["", "", "", ""]
        trustDynamicTexts = ["", "", "", ""]
        trustHistoricTexts = ["", "", "", ""]
        trafficCongestionTexts = ["","","",""]
        weatherDataTexts = ["","","",""]

        for i in range(0, noOfSignals):
            signalTexts[i] = font.render(
                str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i], signalTimerCoods[i])

            displayText = vehicles[directionNumbers[i]]['crossed']

            vehicleCountTexts[i] = font.render(
                str(displayText), True, black, white)
            screen.blit(vehicleCountTexts[i], vehicleCountCoods[i])
            

            trust_color = green
            if congestion[i].trust_dynamic < weightage:
                trust_color = red
            elif congestion[i].trust_dynamic < weightage*2:
                trust_color = yellow

            trustDynamicTexts[i] = font.render(
                str("TRUST : "+str(congestion[i].trust_dynamic)), True, trust_color, black)
            screen.blit(trustDynamicTexts[i], trustHistoricCoords[i])

            # trustHistoricTexts[i] = font.render(
            #     str("H TRUST  : "+str(congestion[i].trust_historic)), True, white, black)
            # screen.blit(trustHistoricTexts[i], trustHistoricCoords[i])


            trafficCongestionTexts[i] = font.render(
                str("Traffic Congestion : "+congestion[i].congestion_time),True, white, black
            )
            screen.blit(trafficCongestionTexts[i], trafficCongestionCoords[i])


            weatherDataTexts[i] = font.render(
                str("Weather : "+congestion[i].weather_description),True, white, black
            )
            screen.blit(weatherDataTexts[i], weatherDataCoords[i])








        timeElapsedText = font.render(
            ("Time Elapsed: "+str(timeElapsed)), True, black, white)
        screen.blit(timeElapsedText, (1100, 50))

        for vehicle in simulation:

            # if((vehicle.x < 0 or vehicle.x > screenWidth) and (vehicle.y < 0 or vehicle.y > screenHeight)):
            #     vehicles[vehicle.direction][vehicle.lane].remove(vehicle)

            # else:
            screen.blit(vehicle.currentImage, [vehicle.x, vehicle.y])
            vehicle.move()

        pygame.display.update()


Main()


# In[ ]:


# In[ ]:
