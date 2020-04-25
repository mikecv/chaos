#!/usr/bin/env python3

# *******************************************
# Colour boundary class for image rendering.
# Boundaries used to define colour bands.
# *******************************************
class colourBoundary():
    def __init__(self, iLim, red, green, blue):

        self.itLimit = iLim
        self.colRed = red
        self.colGreen = green
        self.colBlue = blue
