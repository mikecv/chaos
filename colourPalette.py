#!/usr/bin/env python3

import gi
import math

from colourBoundary import *

# *******************************************
# Class needs Gtk version 3.0.
# *******************************************
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

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

        self.colBoundaries = []
        # Define colour boundaries
        for i in range (0, config["Colours"]["maxBoundries"]):
            self.colBoundaries.append(colourBoundary(0, 0, 0, 0))

        # Initialise to default shades of grey palette with 2 boundaries.
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
        button = self.builder.get_object("ColCancelBtn")
        button.connect('clicked', self.quitEdit)
        button = self.builder.get_object("ColSaveBtn")
        button.connect('clicked', self.saveEdit)

        adjustment = Gtk.Adjustment(0.0, 0.0, self.chaos.maxIterations, 10, 5, 20)
        itScale1 = self.builder.get_object("itScale1")
        itScale1.set_adjustment(adjustment)
        itScale1.set_fill_level(self.chaos.maxIterations)
        itScale1.set_value(self.colBoundaries[0].itLimit)
        itColour1 = self.builder.get_object("itColour1")

        self.winColour.show_all()

    # *******************************************
    # Iteration limit changed callback.
    # *******************************************
    def itLimChanged(self, widget):
        self.logger.debug("Iteration limit changed.")

    # *******************************************
    # Quit edit callback.
    # Do not overwrite original colour palette.
    # *******************************************
    def quitEdit(self, widget):
        self.winColour.hide()

    # *******************************************
    # Save edit callback.
    # Overwrite original colour palette with new one.
    # *******************************************
    def saveEdit(self, widget):
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
