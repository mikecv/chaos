#!/usr/bin/env python3

import logging
import logging.handlers
import gi
import matplotlib.pyplot as plt
from matplotlib.backends.backend_gtk3agg import FigureCanvasGTK3Agg as fc

# *******************************************
# Classes needs Gtk version 3.0.
# *******************************************
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# *******************************************
# Histogram class for iteration divergence histogram.
# *******************************************
class histogramPlot():
    # Initializer / Instance Attributes
    def __init__(self, config, logger, builder, chaos):

        self.config = config
        self.logger = logger
        self.builder = builder
        self.chaos = chaos

        # Create window to hold container matplotlib plot.
        self.winHistogram = self.builder.get_object("histogramWindow")

        # Create Gtk.box to hold matplotlib plot.
        self.histBox = self.builder.get_object("histogramBox")

    def plotHistogram(self):
        # Create the figure to hold the image canvas.
        self.fig = plt.figure()

        # Create the canvas to hold the plot image.
        self.canvas = fc(self.fig)

        # Add the canvas to the box container.
        # First remove any other children (previous plots).
        for child in self.histBox.get_children():
            self.histBox.remove(child)
        self.histBox.pack_start(self.canvas, True, True, 0)

        # Define the histogram plot.
        plt.plot(self.chaos.bins, self.chaos.hist, color='blue', linewidth=1, marker='o', markersize=2)

        # Show the colour palette edit dialog.
        self.winHistogram.show_all()
