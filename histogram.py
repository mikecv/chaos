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

        # Create close button and define callback.
        self.buttonHistClose = self.builder.get_object("histCloseBtn")
        self.buttonHistClose.connect('clicked', self.closeHistogram)

    # *******************************************
    # Plot histogram with current image calculations.
    # *******************************************
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

        # Calculate derivatives.
        # Potentially use them for detecting turning points for colour changes.
        # Not being plotted at this stage.
        firstDeriv = [0 for i in range(self.chaos.maxIterations)]
        for i in range (1, (self.chaos.maxIterations - 1)):
            firstDeriv[i-1] = self.chaos.hist[i] - self.chaos.hist[i-1]

        # Option to not include max iterations in histogram.
        # Depending on the image max iterations can swamp the histogram.
        # Also option to plot as bar graph or as line plot instead.
        if self.chaos.incMaxIterations == True :
            if self.chaos.histLinePlot == True :
                plt.plot(self.chaos.bins, self.chaos.hist, color='blue', linewidth=1, marker='o', markersize=2)
            else:
                plt.bar(self.chaos.bins, self.chaos.hist, color='blue')
        else:
            if self.chaos.histLinePlot == True :
                plt.plot(self.chaos.bins[:-1], self.chaos.hist[:-1], color='blue', linewidth=1, marker='o', markersize=2)
            else:
                plt.bar(self.chaos.bins[:-1], self.chaos.hist[:-1], color='blue')
        plt.xlabel('Iteration on Divergence')
        plt.ylabel('Frequency')
        plt.title('Histogram of Divergence Iterations')

        # Option to use log scale for iteration count axis (y).
        # Depending on the plot can make it easier to read.
        if self.chaos.logItsCounts == True :
            plt.yscale('log')
        plt.minorticks_on()
        plt.tick_params(which='major', length=8, width=2, direction='out')
        plt.tick_params(which='minor', length=4, width=2, direction='out')

        # Show the histogram dialog.
        self.winHistogram.show_all()

    # *******************************************
    # Close histogram plot callback.
    # *******************************************
    def closeHistogram(self, widget):
        # Do nothing, just hide dialog.
        self.winHistogram.hide()
