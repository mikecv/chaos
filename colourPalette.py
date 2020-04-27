#!/usr/bin/env python3

import gi
import math

from utils import *
from colourBoundary import *

# *******************************************
# Classes needs Gtk version 3.0.
# *******************************************
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# *******************************************
# Colour boundary control class
# *******************************************
class boundaryControl():
    # Initializer / Instance Attributes
    def __init__(self, slider, colour):

        self.sliderCtrl = slider
        self.colourCtrl = colour
    
# *******************************************
# Colour palette class for image rendering.
# Palette made out of colour boundaries.
# *******************************************
class colourPalette():
    # Initializer / Instance Attributes
    def __init__(self, config, logger, builder, chaos):

        self.config = config
        self.logger = logger
        self.builder = builder
        self.chaos = chaos

        # Define colour boundaries
        self.colBoundaries = []
        for i in range (0, self.config["Colours"]["maxBoundries"]):
            self.colBoundaries.append(colourBoundary(0, 0, 0, 0))

        # Initialise to default colour palette.
        self.updateColBoundary(1, 1, 0, 0, 200)
        self.updateColBoundary(2, math.floor(self.chaos.maxIterations * 0.20) - 1, 0, 0, 50)
        self.updateColBoundary(3, math.floor(self.chaos.maxIterations * 0.80), 150, 150, 150)
        self.updateColBoundary(4, self.chaos.maxIterations, 0, 0, 0)

    # *******************************************
    # Update colour boundary details.
    # Boundary number is 1 based.
    # *******************************************
    def updateColBoundary(self, boundary, its, red, green, blue):
        # Update colour band details.
        self.colBoundaries[boundary - 1].itLimit = its
        self.colBoundaries[boundary - 1].colRed = red
        self.colBoundaries[boundary - 1].colGreen = green
        self.colBoundaries[boundary - 1].colBlue = blue
        self.logger.debug("Updated colour boundary : {0:d}, iterations : {1:d}, red : {2:d}, green : {2:d}, blue : {2:d}".format(
            boundary, its, red, green, blue))

    # *******************************************
    # Save colour palette to file.
    # *******************************************
    def editPalette(self):
        # Create dialog to edit colour palette.
        self.winColour = self.builder.get_object("colourPaletteWindow")

        # Define button callbacks.
        buttonColCancel = self.builder.get_object("ColCancelBtn")
        buttonColCancel.connect('clicked', self.quitColEdit)
        buttonColSave = self.builder.get_object("ColSaveBtn")
        buttonColSave.connect('clicked', self.saveColEdit)

        # Boundary controls.
        self.boundaryControls = []

        # Set up boundary controls.
        # Get them to match current saved values.
        for i in range (0, self.config["Colours"]["maxBoundries"]):
            self.boundaryControls.append(boundaryControl(self.builder.get_object("itScale{0:d}".format(i+1)), self.builder.get_object("itColour{0:d}".format(i+1))))
            self.boundaryControls[i].sliderCtrl.set_range(0, self.chaos.maxIterations)
            self.boundaryControls[i].sliderCtrl.set_fill_level(self.chaos.maxIterations)
            self.boundaryControls[i].sliderCtrl.set_value(self.colBoundaries[i].itLimit)
            self.boundaryControls[i].colourCtrl.set_rgba(conGdkCol(self.colBoundaries[i].colRed, self.colBoundaries[i].colGreen, self.colBoundaries[i].colBlue, 255))

        # Show the colour palette edit dialog.
        self.winColour.show_all()

    # *******************************************
    # Quit edit callback.
    # Do not overwrite original colour palette.
    # *******************************************
    def quitColEdit(self, widget):
        # Do nothing, just hide dialog.
        self.winColour.hide()

    # *******************************************
    # Save edit callback.
    # Overwrite original colour palette with new one.
    # *******************************************
    def saveColEdit(self, widget):
        # Need to save all the settings to the colour palette.
        for i in range (0, self.config["Colours"]["maxBoundries"]):
            # Get max iterations.
            self.colBoundaries[i].itLimit = int(math.floor(self.boundaryControls[i].sliderCtrl.get_value()))

            # Get component colours.
            # Note that Gdk.colour components in range 0-65535, need to convert to 0-255.
            gdkc = self.boundaryControls[i].colourCtrl.get_color()
            self.colBoundaries[i].colRed = int(math.floor(gdkc.red / 257))
            self.colBoundaries[i].colGreen = int(math.floor(gdkc.green / 257))
            self.colBoundaries[i].colBlue = int(math.floor(gdkc.blue / 257))
    
        # Hide the dialog.
        self.winColour.hide()

    # *******************************************
    # Save colour palette to file.
    # *******************************************
    def saveToFile(self, jFile):
        # Create Json output using dictionary function.
        output = objToDict(self)

        # Open file for writing.
        outfile = open(jFile, 'w')
        outfile.write(json.dumps(output, sort_keys=False, indent=4))
        outfile.close()
        self.logger.info("Saved colour palette file : {0:s}".format(jFile))

    # *******************************************
    # Load colour palette from file.
    # *******************************************
    def loadFromFile(self, jFile):
        try:
            with open(jFile) as cb_file:
                cb = json.load(cb_file)
        except Exception:
            self.logger.info("Failed to open colour palette file : {0:s}".format(jFile))

        self.colBoundaries = []
        cbands = cb["colBoundaries"]
        for cb in cbands:
            self.colBoundaries.append(colourBoundary(cb['itLimit'], cb['colRed'], cb['colGreen'], cb['colBlue']))
        self.logger.info("Loaded colour palette file : {0:s}".format(jFile))
