import re
import time
import json
import threading
from datetime import datetime
import telebot
from telebot import types
import logging
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'#Указать путь до "tesseract.exe" если лежит не по умолчанию, по умолчанию строку удалить'
from io import BytesIO
import socket
import requests
