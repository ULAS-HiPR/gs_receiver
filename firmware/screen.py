import displayio
from adafruit_st7789 import ST7789

class Screen:
    def __init__(self, bus):
        #initializing screen
        self.screen = ST7789(bus, width=240, height=280, colstart=0, rowstart=20, bgr=True,invert=True)
        self.display_group = displayio.Group()
        self.screen.root_group = self.display_group

    def update(self, data):
        pass