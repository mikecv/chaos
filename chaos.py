#!/usr/bin/env python3

import logging
import logging.handlers
import json
import gi
import os.path
import time
from datetime import datetime
from PIL import Image
import matplotlib.pyplot as plt
import struct

from utils import *
from colourPalette import *
from imageCalc import *

# *******************************************
# Program history.
# 0.1   MDC 04/04/2020  Original.
# *******************************************

# Program version.
progVersion = "0.1"

# *******************************************
# Program needs Gtk version 3.0.
# *******************************************
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib

# *******************************************
# Open configuration file for program constants.
# *******************************************
try:
    with open('chaos.json') as config_file:
        config = json.load(config_file)
except Exception:
    print("Failed to open configuration file : {0:s}".format('chaos.json'))
    exit(-1)

# *******************************************
# Create logger.
# Use rotating log files.
# *******************************************
logger = logging.getLogger('chaos')
logger.setLevel(config["DebugLevel"])
handler = logging.handlers.RotatingFileHandler('chaos.log', maxBytes=config["LogFileSize"], backupCount=config["LogBackups"])
handler.setFormatter(logging.Formatter(fmt='%(asctime)s.%(msecs)03d [%(name)s] [%(levelname)-8s] %(message)s', datefmt='%Y%m%d-%H:%M:%S', style='%'))
logging.Formatter.converter = time.localtime
logger.addHandler(handler)

# Log program version.
logger.info("Program version : {0:s}".format(progVersion))

# ****************************s***************
# Load css style sheet for window decorations.
# *******************************************
css_provider = Gtk.CssProvider()
css_provider.load_from_path('./chaos.css')
Gtk.StyleContext.add_provider_for_screen(
    Gdk.Screen.get_default(),
    css_provider,
    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
)

# *******************************************
# GUI handler class.
# *******************************************
class Handler:
    def onDestroy(self, *args):
        Gtk.main_quit()

# *******************************************
# Chaos class.
# *******************************************
class Mandelbrot():
    # Initializer / Instance Attributes
    def __init__(self, window):

        self.myWindow = window

        # Image size in pixles.
        self.imageWidth = config["Image"]["imageWidth"]
        self.imageHeight = config["Image"]["imageHeight"]

        # Image colour bits.
        self.imageColours = config["Image"]["colourBits"]
        # Number of iterations to use for calculations.
        self.maxIterations = config["Calculations"]["DefMaxIterations"]

        # Array to hold iteration counts.
        self.iterations = [[0 for i in range(self.imageWidth)] for j in range(self.imageHeight)]
        self.histLinePlot = config["Colours"]["histLinePlot"]
        self.incMaxIterations = config["Colours"]["includeMaxIts"]
        self.logItsCounts = config["Colours"]["logItsCounts"]
 
        # Array to hold histogram information.
        self.bins = [(i + 1) for i in range(self.maxIterations)]
        self.hist = [0 for i in range(self.maxIterations)]
        self.lowBin = 0

        # Colour palette for rendering.
        self.palette = colourPalette(config, logger, builder, self)
 
        # Rendering flag black or colour palette.
        self.black = config["Colours"]["renderBlack"]
 
        # Image generation time.
        self.genTime = ""

        # Set up the Help/About menu item response.
        aboutItem = builder.get_object("AboutItem")
        aboutItem.connect('activate', self.about)

        # Set up the New Image menu item and toolbar icon and response.
        imgNewItem = builder.get_object("ImageNewItem")
        imgNewItem.connect('activate', self.newPic)
        imgNewTool = builder.get_object("ImageNewTool")
        imgNewTool.connect('clicked', self.newPic)

        # Set up the Load Image Data menu item and toolbar icon and response.
        imgDataLoadItem = builder.get_object("ImageLoadDataItem")
        imgDataLoadItem.connect('activate', self.loadPicData)
        imgDataLoadTool = builder.get_object("ImageLoadDataTool")
        imgDataLoadTool.connect('clicked', self.loadPicData)

        # Set up the Save Image Data menu item and toolbar icon and response.
        imgDataSaveItem = builder.get_object("ImageSaveDataItem")
        imgDataSaveItem.connect('activate', self.savePicData)
        imgDataSaveTool = builder.get_object("ImageSaveDataTool")
        imgDataSaveTool.connect('clicked', self.savePicData)

        # Set up the Save Image menu item and toolbar icon and response.
        imgSaveItem = builder.get_object("ImageSaveItem")
        imgSaveItem.connect('activate', self.savePic)
        imgSaveTool = builder.get_object("ImageSaveTool")
        imgSaveTool.connect('clicked', self.savePic)

        # Set up the View / Zoom menu item and toolbar icon and response.
        zoomItem = builder.get_object("ZoomItem")
        zoomItem.connect('activate', self.zoom)
        zoomTool = builder.get_object("ZoomTool")
        zoomTool.connect('clicked', self.zoom)

        # Set up container to hold zoom factor slider.
        zoomBox = builder.get_object("zoomBox")

        # Set up zoom value slider.
        self.zoomFactor = 1.0
        self.zoomSlider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.zoomSlider.set_range(0, 25.0)
        self.zoomSlider.set_value_pos(Gtk.PositionType.BOTTOM)
        self.zoomSlider.add_mark(0.0, Gtk.PositionType.BOTTOM, '0')
        self.zoomSlider.add_mark(5.0, Gtk.PositionType.BOTTOM, '5')
        self.zoomSlider.add_mark(10.0, Gtk.PositionType.BOTTOM, '10')
        self.zoomSlider.add_mark(15.0, Gtk.PositionType.BOTTOM, '15')
        self.zoomSlider.add_mark(20.0, Gtk.PositionType.BOTTOM, '20')
        self.zoomSlider.add_mark(25.0, Gtk.PositionType.BOTTOM, '25')
        self.zoomSlider.set_value(self.zoomFactor)
        self.zoomSlider.connect("value-changed", self.ScaleChange)
        zoomBox.add(self.zoomSlider)

        # Set up the View / Re-centre window menu item and toolbar icon and response.
        recentreItem = builder.get_object("RecentreItem")
        recentreItem.connect('activate', self.recentrePic)
        recentreTool = builder.get_object("RecentreTool")
        recentreTool.connect('clicked', self.recentrePic)

        # Set up the View / Redraw image menu item and toolbar icon and response.
        redrawItem = builder.get_object("RedrawItem")
        redrawItem.connect('activate', self.rerenderPic)
        redrawTool = builder.get_object("RedrawTool")
        redrawTool.connect('clicked', self.rerenderPic)

        # Set up the View / Set maximum iterations menu item and toolbar icon and response.
        self.MaxItsItem = builder.get_object("SetMaxIterationsItem")
        self.MaxItsItem.connect('activate', self.setMaxIterations)
        self.MaxItsTool = builder.get_object("SetMaxIterationsTool")
        self.MaxItsTool.connect('clicked', self.setMaxIterations)

        # Set up the View / Recalculate Image menu item and toolbar icon and response.
        RecalculateItem = builder.get_object("RecalculateItem")
        RecalculateItem.connect('activate', self.recalculateImage)
        RecalculateTool = builder.get_object("RecalculateTool")
        RecalculateTool.connect('clicked', self.recalculateImage)

        # Set up the Colour Palette / Load menu item and toolbar icon and response.
        colLoadItem = builder.get_object("LoadPaletteItem")
        colLoadItem.connect('activate', self.loadColourPalette)
        colLoadTool = builder.get_object("LoadPaletteTool")
        colLoadTool.connect('clicked', self.loadColourPalette)

        # Set up the Colour Palette/Save menu item and toolbar icon and response.
        colSaveItem = builder.get_object("SavePaletteItem")
        colSaveItem.connect('activate', self.saveColourPalette)
        colSaveTool = builder.get_object("SavePaletteTool")
        colSaveTool.connect('clicked', self.saveColourPalette)

        # Set up the Colour Palette/Edit menu item and toolbar icon and response.
        self.colEditItem = builder.get_object("EditPaletteItem")
        self.colEditItem.connect('activate', self.editColourPalette)
        self.colEditTool = builder.get_object("EditPaletteTool")
        self.colEditTool.connect('clicked', self.editColourPalette)

        # Set up the Colour Plot Histogram menu item and toolbar icon and response.
        self.plotHistogramItem = builder.get_object("PlotHistogramItem")
        self.plotHistogramItem.connect('activate', self.plotHistogram)
        self.plotHistogramTool = builder.get_object("PlotHistogramTool")
        self.plotHistogramTool.connect('clicked', self.plotHistogram)

        # Set up right details pane.
        self.centrePtRealLbl = builder.get_object("centrePtRealLbl")
        self.centrePtImagLbl = builder.get_object("centrePtImagLbl")
        self.pixelSizeLbl = builder.get_object("pixelSizeLbl")
        self.imageScaleLbl = builder.get_object("imageScaleLbl")
        self.imageFrameSizeLbl = builder.get_object("imageFrameSizeLbl")
        self.imageSizeLbl = builder.get_object("imageSizeLbl")
        self.maxIterationsLbl = builder.get_object("maxIterationsLbl")

        # Set up right detial controls and initial status.
        self.colourRenderCtrl = builder.get_object("colourRenderCtrl")
        self.colourRenderCtrl.connect("notify::active", self.colourSwitchActivated)
        self.colourRenderCtrl.set_state(not self.black)
        self.histogramLinePlotCtrl = builder.get_object("histogramLinePlotCtrl")
        self.histogramLinePlotCtrl.connect("notify::active", self.linePlotSwitchActivated)
        self.histogramLinePlotCtrl.set_state(self.histLinePlot)
        self.histogramLogScaleCtrl = builder.get_object("histogramLogScaleCtrl")
        self.histogramLogScaleCtrl.connect("notify::active", self.logScaleSwitchActivated)
        self.histogramLogScaleCtrl.set_state(self.logItsCounts)

        # Set up the quit menu and toolbar icon item response.
        # Just call Gtk quit method.
        quitItem = builder.get_object("QuitItem")
        quitItem.connect('activate', Gtk.main_quit)
        quitTool = builder.get_object("QuitTool")
        quitTool.connect('clicked', Gtk.main_quit)

        # Set up the status bar.
        self.statusbar = builder.get_object("statusBar")
        self.context_id = self.statusbar.get_context_id("statusBar")

        # Initialise pic to blank image.
        self.initPic()

        # Set up event box associated with the image container.
        self.picEventBox = builder.get_object("picEventBox")

        # Update image data and processing status.
        self.updateInfo()

    # *******************************************
    # Update image data and processing information/status.
    # *******************************************
    def updateInfo(self):
        # Update image information.
        self.centrePtRealLbl.set_text("{0:0.15e}".format(self.centreReal))
        self.centrePtImagLbl.set_text("{0:0.15e}".format(self.centreImag))
        self.pixelSizeLbl.set_text("{0:0.15e}".format(self.pxSize))
        self.imageScaleLbl.set_text("{0:0.15e}".format(self.imageScale))
        self.imageFrameSizeLbl.set_text("{0:d} x {1:d}".format(self.picFrameWidth, self.picFrameHeight))
        self.imageSizeLbl.set_text("{0:d} x {1:d}".format(self.imageWidth, self.imageHeight))
        self.maxIterationsLbl.set_text("{0:d}".format(self.maxIterations))

    # *******************************************
    # Block menu items if image generation in progress, i.e. not idle.
    # Prevents variables that imageCalc requires from changing.
    # *******************************************
    def blockMenus(self, idle):
        # Block menus as necessary if calculations in progress.

        # Inhibit/Enable some menu items during image generation.
        self.MaxItsItem.set_sensitive(idle)
        self.MaxItsTool.set_sensitive(idle)
        self.colEditItem.set_sensitive(idle)
        self.colEditTool.set_sensitive(idle)
        self.plotHistogramItem.set_sensitive(idle)
        self.plotHistogramTool.set_sensitive(idle)

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # Zoom image at the current centre at the current zoom factor level.
    # *******************************************
    def zoom(self, widget):
        logger.debug("Image zoom selected at zoom factor : {0:f}".format(self.zoomFactor))

        # Update status bar to wait for image.
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Zooming image, please wait...")

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

        # Update pixel size and overall image scale.
        self.pxSize = self.pxSize / self.zoomFactor
        self.imageScale = self.imageScale * self.zoomFactor
        logger.debug("Image pixel size : {0:f}".format(self.pxSize))
        logger.debug("Image scale : {0:f}".format(self.imageScale))

        # Generate zoomed image at current centre.
        self.genImage((0, self.imageHeight - 1), (0, self.imageWidth - 1))
        self.renderImage(self.black)

        # Update image data following image generation.
        self.updateInfo()

        # Update status bar to wait for image.
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "New image generation complete in : {0:s}".format(self.genTime))

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # Zoom scale changed on slider.
    # *******************************************
    def ScaleChange(self, widget):
        # Set zoom factor to current value of slider.
        self.zoomFactor = widget.get_value()

    # *******************************************
    # Render colour switch activated.
    # *******************************************
    def colourSwitchActivated(self, widget, gparam):
        # Check state of switch and update variable.
        self.black = not widget.get_active()

    # *******************************************
    # Histogram line plot switch activated.
    # *******************************************
    def linePlotSwitchActivated(self, widget, gparam):
        # Check state of switch and update variable.
        self.histLinePlot = widget.get_active()

    # *******************************************
    # Histogram integration count axis log scale switch activated.
    # *******************************************
    def logScaleSwitchActivated(self, widget, gparam):
        # Check state of switch and update variable.
        self.logItsCounts = widget.get_active()

    # *******************************************
    # Recentre image.
    # *******************************************
    def recentrePic(self, widget):
        # Connect mouse pressed event.
        self.cid = self.picEventBox.connect('button-press-event', self.recentreMouse)

        # Update status bar to instruct user to seclect centre position
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Click mouse button to select new centre for image...")

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # Recentre mouse handler
    # *******************************************
    def recentreMouse(self, widget, event):
        logger.debug("Image recentre selected at ({0:d}, {1:d})".format(int(event.x), int(event.y)))

        # Apply offset to get selected pointed into image coordinates.
        picCentreX = int(event.x) - self.imageStartX
        picCentreY = int(event.y) - self.imageStartY

        # Check that the point is in the image area.
        if ((picCentreX > 0) and (picCentreX < self.imageWidth) and (picCentreY > 0) and (picCentreY < self.imageHeight)):
            # Disconnect mouse pressed event.
            self.picEventBox.disconnect(self.cid)

            # Update status bar to wait for image.
            self.statusbar.pop(self.context_id)
            self.statusbar.push(self.context_id, "Recentering image to ({0:d}, {1:d}), please wait...".format(picCentreX, picCentreY))

            # Check for Gtk events. Required to update status bar now.
            while Gtk.events_pending():
                Gtk.main_iteration()

            # Determine how many pixels to move current image.
            # Positive amount centre moved down or to the right, negative amount centre moved up or to the left.
            self.horizontalMove = picCentreX - self.centrePxX
            self.verticalMove = picCentreY - self.centrePxY
            logger.debug("Image centre translation, horizontal : {0:d}, vertical {1:d}".format(self.horizontalMove, self.verticalMove))

            # Determine new centre for image.
            self.centreReal += (self.horizontalMove * self.pxSize)
            self.centreImag -= (self.verticalMove * self.pxSize)

            self.moveImage(self.horizontalMove, self.verticalMove)
            #self.genImage((0, self.imageHeight - 1), (0, self.imageWidth - 1))
            self.renderImage(self.black)

            # Update image data following recentring.
            self.updateInfo()

            # Update status bar to wait for image.
            self.statusbar.pop(self.context_id)
            self.statusbar.push(self.context_id, "Image recentre complete in : {0:s}".format(self.genTime))

            # Check for Gtk events. Required to update status bar now.
            while Gtk.events_pending():
                Gtk.main_iteration()

    # *******************************************
    # Rerender the image.
    # Uses the current calculated image, and the latest colour palette and rendering settings.
    # *******************************************
    def rerenderPic(self, widget):
        logger.debug("Image redraw selected, please wait...")

        # Rerender the image.
        self.renderImage(self.black)

        # Update image data.
        self.updateInfo()

        # Update status bar to instruct user to seclect centre position
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Image redraw complete.")

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # Allow user to set the maximum iteration limit for the image.
    # *******************************************
    def setMaxIterations(self, widget):
        # Create dialog to set maximum iterations.
        self.itsedit = builder.get_object("itsEntryDialog")

        # Define button callbacks.
        buttonItsCancel = builder.get_object("cancelItsBtn")
        buttonItsCancel.connect('clicked', self.quitMaxIts)
        buttonItsSave = builder.get_object("acceptItsBtn")
        buttonItsSave.connect('clicked', self.saveMaxIts)

        # Define the maximum iterations entry field.
        self.maxItsEntry = builder.get_object("maxItsEntry")
        # Set the entry to be the current maximum iteration count.
        self.maxItsEntry.set_text(str(self.maxIterations))

        # Define warning text label.
        self.warnText = builder.get_object("itsWarning")
        self.warnText.set_text("")

        # Show the maximum iterations edit dialog.
        self.itsedit.show_all()

    # *******************************************
    # Quit edit callback.
    # Do not overwrite current maximum iterations.
    # *******************************************
    def quitMaxIts(self, widget):
        # Do nothing, just hide dialog.
        self.warnText.set_text("")
        self.itsedit.hide()

    # *******************************************
    # Save edit callback.
    # Overwrite maximum iteration value.
    # *******************************************
    def saveMaxIts(self, widget):
        # Red the value of the 
        usrEntry = self.maxItsEntry.get_text()

        # Check if the entry is an integer.
        try: 
            mi = int(usrEntry)
            if (mi > 0):
                self.warnText.set_text("")
                self.itsedit.hide()

                self.maxIterations = mi
                self.itsedit.hide()
                self.updateInfo()
            else:
                # Integer entered but not greater than 0, warning.
                self.warnText.set_markup("<span foreground=\"red\">"
                    + "Not a valid maximum iterations count.\n"
                    + "Please enter an integer greater than 0."
                    + "</span>"
                )
        except ValueError:
            # Not a valid integer, warning.
                self.warnText.set_markup("<span foreground=\"red\">"
                    + "Not a valid maximum iterations count.\n"
                    + "Please enter an integer greater than 0."
                    + "</span>"
                )

    # *******************************************
    # Recalculate the image.
    # Regenerate the image with the current setting and zoom factor or 1.0.
    # This is used to regenerate the same image after max iterations has changed.
    # *******************************************
    def recalculateImage(self, widget):
        logger.debug("Image recalculation selected, please wait...")

        # Update status bar to wait for image.
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Recalculating image, please wait...")

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

        # Generate zoomed image at current centre.
        self.genImage((0, self.imageHeight - 1), (0, self.imageWidth - 1))
        self.renderImage(self.black)

        # Update image data following image generation.
        self.updateInfo()

        # Update status bar to wait for image.
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Image recalculation complete in : {0:s}".format(self.genTime))

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # File/New menu item selected.
    # Starts off with the default Mandlebrot plot.
    # *******************************************
    def initPic(self):
        # Create pixel buffer for manipulating image.
        # Initialise buffer to all white (alpha channel ff (not used)).
        pixbuf = GdkPixbuf.Pixbuf.new(colorspace = GdkPixbuf.Colorspace.RGB, has_alpha = False, bits_per_sample = self.imageColours, width = self.imageWidth, height = self.imageHeight)
        pixbuf.fill(0xffffffff)
        logger.debug("Created Gdk pixel buffer of type : {0:s}".format(str(type(pixbuf))))
        width, height = pixbuf.get_width(), pixbuf.get_height()
        logger.debug("Gtk image frame width : {0:d}, frame height : {1:d}".format(width, height))

        # Associate pixel buffer with main image and show.
        self.gtkPic = builder.get_object("mainImage")
        # Get requested size, which will be maximum size.
        self.picFrameWidth = self.gtkPic.size_request().width
        self.picFrameHeight = self.gtkPic.size_request().height
        logger.debug("Gtk image width : {0:d}, height : {1:d}".format(self.picFrameWidth, self.picFrameHeight))

        # If image is smaller than image frame then need to check that we are pointing to the image.
        self.imageStartX = math.floor((self.picFrameWidth - self.imageWidth) / 2)
        self.imageEndX = self.imageStartX + self.imageWidth
        self.imageStartY = math.floor((self.picFrameHeight - self.imageHeight) / 2)
        self.imageEndY = self.imageStartY + self.imageHeight
        logger.debug("Image in frame coordinates (x, y) start : ({0:d}, {1:d}), end : {2:d}, {3:d})".format(self.imageStartX, self.imageEndX, self.imageStartY, self.imageEndY))

        # Load gtk image form Pixbuf.
        self.gtkPic.set_from_pixbuf(pixbuf)
        width, height = pixbuf.get_width(), pixbuf.get_height()
        logger.debug("Created Gtk image of type : {0:s}, width : {1:d}, height : {2:d}".format(str(type(self.gtkPic)), width, height))

        # Create PIL image version as seems easier to manipulate at pixel level.
        self.pilPic = Image.frombytes("RGB", (width, height), pixbuf.get_pixels())
        logger.debug("Created PIL image of type : {0:s}".format(str(type(self.pilPic))))

        # Image coordinates and scale.
        self.centreReal = config["Calculations"]["DefCentreReal"]
        self.centreImag = config["Calculations"]["DefCentreImag"]
        self.pxSize = config["Calculations"]["DefPixelSize"]
        self.imageScale = config["Calculations"]["DefScale"]

        logger.debug("Image centre REAL : {0:f}".format(self.centreReal))
        logger.debug("Image centre IMAGINARY : {0:f}".format(self.centreImag))
        logger.debug("Image pixel size : {0:f}".format(self.pxSize))
        logger.debug("Image scale : {0:f}".format(self.imageScale))

        # Centre pixel for purposes of recentering.
        self.centrePxX = math.floor(self.imageWidth / 2)
        self.centrePxY = math.floor(self.imageHeight / 2)

    # *******************************************
    # New image control selected.
    # Starts off with the default Mandlebrot plot.
    # *******************************************
    def newPic(self, widget):
        logger.debug("User selected new image control.")

        # Inhibit the some menu items during image generation.
        self.blockMenus(False)

        # Initialise pic to blank image.
        self.initPic()

        # Update status bar to wait for image.
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Generating default image, please wait...")

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

        # Generate the initial image.
        # Initial image parameters already set up.
        self.genImage((0, self.imageHeight - 1), (0, self.imageWidth - 1))
        self.renderImage(self.black)

        # Update image data following recentring.
        self.updateInfo()

        # Update status bar to wait for image.
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "New image generation complete in : {0:s}".format(self.genTime))

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

        # Enable menu items inhibited during image generation.
        self.blockMenus(True)

    # *******************************************
    # Load image data control selected.
    # *******************************************
    def loadPicData(self, widget):
        logger.debug("User selected load image data control.")

        # Inhibit the some menu items during image generation.
        self.blockMenus(False)

        # Start time for image generation timing.
        startTime = datetime.now()

        # Launch dialog to select file to read from.
        dlg = Gtk.FileChooserDialog("Load image data...", self.myWindow, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        f = Gtk.FileFilter()
        f.set_name("DAT Files")
        f.add_pattern("*.dat")
        dlg.add_filter(f)
        response = dlg.run()

        # Check for positive response, and get filename.
        fname = ""
        if ((response == Gtk.ResponseType.OK) or (response == Gtk.STOCK_OPEN)):
            fname = dlg.get_filename()
        
        # Destroy dialog.
        dlg.destroy()

        # If have a filename then open.
        if fname != "":

            # Open file for binary write.
            bf = open(fname, 'rb')

            # Read image size from file.
            dataWidth = struct.unpack('i', bf.read(4))[0]
            dataHeight = struct.unpack('i', bf.read(4))[0]
            # Check if iterations array needs to be resized.
            if ((dataWidth != self.imageWidth) or (dataHeight != self.imageHeight)):
                # Resize the array to suit data.
                logger.debug("Resizing iterations array to width : {0:d}, height : {1:d}".format(dataWidth, dataHeight))
                self.iterations = [[0 for i in range(dataWidth)] for j in range(dataHeight)]
                self.imageWidth = dataWidth
                self.imageHeight = dataHeight
                # Initialise image as size changed.
                self.initPic()
            else:
                self.imageWidth = dataWidth
                self.imageHeight = dataHeight

            # Read max iterations from file.
            dataIterations = struct.unpack('i', bf.read(4))[0]
            # Resize space required for histogram if required.
            if (dataIterations != self.maxIterations):
                logger.debug("Resizing histogram arrays to dimension : {0:d}".format(dataIterations))
                self.bins = [(i + 1) for i in range(dataIterations)]
                self.hist = [0 for i in range(dataIterations)]
            # Update maximum iterations.
            self.maxIterations = dataIterations

            # Read image centre from file.
            self.centreReal = struct.unpack('f', bf.read(4))[0]
            self.centreImag = struct.unpack('f', bf.read(4))[0]
            # Read pixel size from file.
            self.pxSize = struct.unpack('f', bf.read(4))[0]
            # Read image scale from file.
            self.imageScale = struct.unpack('f', bf.read(4))[0]

            # Read iteration data from the file.
            for r in range (0, self.imageHeight):
                for c in range (0, self.imageWidth):
                    self.iterations[r][c] = struct.unpack('f', bf.read(4))[0]

            # Close binary file.
            bf.close()

            self.renderImage(self.black)

            # Update image information.
            self.updateInfo()

            # End time and image generation elapsed time.
            endTime = datetime.now()
            self.genTime = "{0:s}".format(str(endTime - startTime))

            # Update status bar to wait for image.
            self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Loaded image and completed render in : {0:s}".format(self.genTime))

        # Enable menu items inhibited during image generation.
        self.blockMenus(True)

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # Save image data control selected.
    # *******************************************
    def savePicData(self, widget):
        logger.debug("User selected save image data control.")

        # Launch dialog to select file to save to.
        dlg = Gtk.FileChooserDialog("Save image data...", self.myWindow, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        f = Gtk.FileFilter()
        f.set_name("DAT Files")
        f.add_pattern("*.dat")
        dlg.add_filter(f)
        response = dlg.run()

        # Check for positive response, and get filename.
        fname = ""
        if ((response == Gtk.ResponseType.OK) or (response == Gtk.STOCK_SAVE)):
            fname = dlg.get_filename()
        
        # Destroy dialog.
        dlg.destroy()

        # If have a filename then save.
        if fname != "":

            # Force to PNG files
            pre, ext = os.path.splitext(fname)
            fname = pre + '.dat'

            # Open file for binary write.
            bf = open(fname, 'wb')

            # Write image size to file.
            bf.write(struct.pack('i', self.imageWidth))
            bf.write(struct.pack('i', self.imageHeight))
            # Write max iterations to file.
            bf.write(struct.pack('i', self.maxIterations))
            # Write image centre to file.
            bf.write(struct.pack('f', self.centreReal))
            bf.write(struct.pack('f', self.centreImag))
            # Write pixel size to file.
            bf.write(struct.pack('f', self.pxSize))
            # Write image scale to file.
            bf.write(struct.pack('f', self.imageScale))

            # Write iteration data to the file.
            for r in range (0, self.imageHeight):
                for c in range (0, self.imageWidth):
                    bf.write(struct.pack('f', self.iterations[r][c]))

            # Close binary file.
            bf.close()

            # Update status bar to wait for image.
            self.statusbar.pop(self.context_id)
            self.statusbar.push(self.context_id, "Image data saved to : {0:s}".format(fname))

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # Save image control selected.
    # *******************************************
    def savePic(self, widget):
        logger.debug("User selected save image control.")

        # Launch dialog to select file to save to.
        dlg = Gtk.FileChooserDialog("Save image...", self.myWindow, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        f = Gtk.FileFilter()
        f.set_name("PNG Files")
        f.add_pattern("*.png")
        dlg.add_filter(f)
        response = dlg.run()

        # Check for positive response, and get filename.
        fname = ""
        if ((response == Gtk.ResponseType.OK) or (response == Gtk.STOCK_SAVE)):
            fname = dlg.get_filename()
        
        # Destroy dialog.
        dlg.destroy()

        # If have a filename then save.
        if fname != "":

            # Force to PNG files
            pre, ext = os.path.splitext(fname)
            fname = pre + '.png'

            self.pilPic.save(fname)

        # Update status bar to wait for image.
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Image saved to : {0:s}".format(fname))

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # Load colour palette control selected.
    # *******************************************
    def loadColourPalette(self, widget):
        logger.debug("User selected load colour palette control.")

        # Launch dialog to select file to read from.
        dlg = Gtk.FileChooserDialog("Open...", self.myWindow, Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        f = Gtk.FileFilter()
        f.set_name("JSON Files")
        f.add_pattern("*.json")
        dlg.add_filter(f)
        response = dlg.run()

        # Check for positive response, and get filename.
        fname = ""
        if ((response == Gtk.ResponseType.OK) or (response == Gtk.STOCK_OPEN)):
            fname = dlg.get_filename()
        
        # Destroy dialog.
        dlg.destroy()

        # If have a filename then open.
        if fname != "":
            self.palette.loadFromFile(fname)

        # Update status bar to wait for image.
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Loaded colour palette : {0:s}".format(fname))

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # Save colour palette control selected.
    # *******************************************
    def saveColourPalette(self, widget):
        logger.debug("User selected save colour palette control.")

        # Launch dialog to select file to save to.
        dlg = Gtk.FileChooserDialog("Save...", self.myWindow, Gtk.FileChooserAction.SAVE,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_SAVE, Gtk.ResponseType.OK))
        f = Gtk.FileFilter()
        f.set_name("JSON Files")
        f.add_pattern("*.json")
        dlg.add_filter(f)
        response = dlg.run()

        # Check for positive response, and get filename.
        if ((response == Gtk.ResponseType.OK) or (response == Gtk.STOCK_SAVE)):
            fname = dlg.get_filename()
        
        # Destroy dialog.
        dlg.destroy()

        # If have a filename then save.
        if fname != "":

            # Force to Json files
            pre, ext = os.path.splitext(fname)
            fname = pre + '.json'

            # Save palette file.
            self.palette.saveToFile(fname)

        # Update status bar to wait for image.
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Colour palette saved to : {0:s}".format(fname))

        # Check for Gtk events. Required to update status bar now.
        while Gtk.events_pending():
            Gtk.main_iteration()

    # *******************************************
    # Edit colour palette control selected.
    # *******************************************
    def editColourPalette(self, widget):
        logger.debug("User selected edit colour palette control.")

        self.palette.editPalette()

    # *******************************************
    # Plot colour histogram control selected.
    # *******************************************
    def plotHistogram(self, widget):
        logger.debug("User selected plot histogram control.")

        # Need to put iterations counts into bins for histogram.
        self.doHistogramBins()

        # Calculate derivatives.
        # Potentially use them for detecting turning points for colour changes.
        # Not being plotted at this stage.
        firstDeriv = [0 for i in range(self.maxIterations)]
        for i in range (1, (self.maxIterations - 1)):
            firstDeriv[i-1] = self.hist[i] - self.hist[i-1]

        fig = plt.figure()
        # Option to not include max iterations in histogram.
        # Depending on the image max iterations can swamp the histogram.
        # Also option to plot as bar graph or as line plot instead.
        if self.incMaxIterations == True :
            if self.histLinePlot == True :
                plt.plot(self.bins, self.hist, color='blue', linewidth=1, marker='o', markersize=2)
            else:
                plt.bar(self.bins, self.hist, color='blue')
        else:
            if self.histLinePlot == True :
                plt.plot(self.bins[:-1], self.hist[:-1], color='blue', linewidth=1, marker='o', markersize=2)
            else:
                plt.bar(self.bins[:-1], self.hist[:-1], color='blue')
        plt.xlabel('Iterations')
        plt.ylabel('Frequency')
        plt.title('Histogram of Divergence Iterations')
        # Option to use log scale for iteration count axis (y).
        # Depending on the plot can make it easier to read.
        if self.logItsCounts == True :
            plt.yscale('log')
        plt.minorticks_on()
        plt.tick_params(which='major', length=8, width=2, direction='out')
        plt.tick_params(which='minor', length=4, width=2, direction='out')
        plt.show()

        # Update status bar to instruct user to seclect centre position
        self.statusbar.pop(self.context_id)
        self.statusbar.push(self.context_id, "Histogram of divergence iteration counts...")

    # *******************************************
    # Put iteration data into bins.
    # *******************************************
    def doHistogramBins(self):

        # Reinitialise histogram bins as max iterations may have changed.
        self.bins = [(i + 1) for i in range(self.maxIterations)]
        self.hist = [0 for i in range(self.maxIterations)]
        self.lowBin = 0

        # Need to get iterations into single array of iteration occurances.
        for bin in range (0, self.maxIterations):
            self.hist[bin] = 0
        for r in range (0, self.imageHeight):
            for c in range (0, self.imageWidth):
                bin = math.floor(self.iterations[r][c]) - 1
                self.hist[bin] += 1

        # Look for lowest non-zero bin.
        # Used for black rendering to maximize colour range.
        for i, bin in enumerate(self.hist):
            if bin > 0:
                break
        self.lowBin = i
        logger.debug("Lowest non-zero bin for iteration histogram : {0:d}".format(self.lowBin))

    # *******************************************
    # Help/About control selected.
    # Displays an "About" dialog box.
    # *******************************************
    def about(self, widget):
        logger.debug("User selected Help/About control.")

        helpDialog = Gtk.MessageDialog(
            parent = self.myWindow,
            flags = Gtk.DialogFlags.MODAL | Gtk.DialogFlags.DESTROY_WITH_PARENT,
            type = Gtk.MessageType.INFO,
            buttons = Gtk.ButtonsType.OK,
            message_format = "CHAOS")
        img = Gtk.Image()
        img.set_from_file("about.png")
        img.show()
        helpDialog.set_image(img)
        helpDialog.format_secondary_markup("Version : {0:s}\n\nMDC 2020".format(progVersion))
        helpDialog.run()
        helpDialog.destroy()

    # *******************************************
    # Method to generate the Mandlebrot image.
    # Performs calculations for the image.
    # Image calculation works on row/column ranges, i.e. a box.
    # Complete image so specify full image size for row/column ranges.
    # *******************************************
    def genImage(self, rowRange, colRange):
        # Start time for image generation timing.
        startTime = datetime.now()

        # Launch thread to calculate image.
        imageThread = imageCalc(1, "CalcImage", logger, self, rowRange, colRange)
        imageThread.start()

        # Wait for thread to end.
        # Check until only 1 thread left; sleep inbetween checks.
        while (threading.active_count() > 1):
            time.sleep(config["Calculations"]["ThreadChkDelay"])

        # End time and image generation elapsed time.
        endTime = datetime.now()
        self.genTime = "{0:s}".format(str(endTime - startTime))

    # *******************************************
    # Method to move an image.
    # Like method to generate whole image except does move first
    # to save time by avoiding recomputation.
    # *******************************************
    def moveImage(self, hMove, vMove):
        # Inhibit the some menu items during image generation.
        self.blockMenus(False)

        # Start time for image generation timing.
        startTime = datetime.now()

        # Do the moves first.
        # Then follow up by recalculating the new bits.
        if hMove < 0:
            # Centre moved left.
            for row in range (0, self.imageHeight):
                for col in range (self.imageWidth - 1, abs(hMove), -1):
                    self.iterations[row][col] = self.iterations[row][col - abs(hMove)]
        elif hMove > 0:
            # Centre moved right.
            for row in range (0, self.imageHeight):
                for col in range (0, (self.imageWidth - abs(hMove) - 1)):
                    self.iterations[row][col] = self.iterations[row][col + abs(hMove)]
        if vMove < 0:
            # Centre moved up.
            for col in range (0, self.imageWidth):
                for row in range (self.imageHeight - 1, abs(vMove), -1):
                    self.iterations[row][col] = self.iterations[row - abs(vMove)][col]
        elif vMove > 0:
            # Centre moved down.
            for col in range (0, self.imageWidth):
                for row in range (0, (self.imageHeight - abs(vMove) - 1)):
                    self.iterations[row][col] = self.iterations[row + abs(vMove)][col]

        # Now that moves of existing calculations have been done,
        # need to regenerate images for missed bits.

        # Regenerate the boxes of data moved.
        if hMove < 0:
            self.genImage((0, self.imageHeight - 1), (0, abs(hMove) + 1))
        elif hMove > 0:
            self.genImage((0, self.imageHeight - 1), (self.imageWidth - abs(hMove) - 1, self.imageWidth - 1))
        if vMove < 0:
            self.genImage((0, abs(vMove) + 1), (0, self.imageWidth - 1))
        elif vMove > 0:
            self.genImage((self.imageHeight - abs(vMove) - 1, self.imageHeight - 1), (0, self.imageWidth - 1))

        # End time and image generation elapsed time.
        endTime = datetime.now()
        self.genTime = "{0:s}".format(str(endTime - startTime))

        # Enable menu items inhibited during image generation.
        self.blockMenus(True)
    
    # *******************************************
    # Method to render the Mandlebrot image.
    # Renders to current colour mapping.
    # Option exists to render in black without palette.
    # *******************************************
    def renderImage(self, black):
        # Quick look through colour palette boundaries to check for useful boundaries.
        # Not useful if iteration limits are not increasing.
        prevBound = -1
        numBoundaries = len(self.palette.colBoundaries)
        useFulBoundaries = 0
        for b in range (0, numBoundaries):
            thisBound = self.palette.colBoundaries[b].itLimit
            logger.debug("PREV bound : {0:d}, THIS bound: {1:d}".format(prevBound, thisBound))
            if prevBound < thisBound:
                prevBound = thisBound
                useFulBoundaries += 1
            else:
                break
        logger.debug("Useful colour palette boundaries : {0:d}, total boundaries : {1:d}".format(useFulBoundaries, numBoundaries))

        # Need to put iterations counts into bins for histogram.
        # This also gets lowest iteration bin used for black renders.
        if black:
            self.doHistogramBins()

        # Set the pixels in the PIL image.
        for row in range (0, self.imageHeight):
            for col in range (0, self.imageWidth):

                # Check if rendering in black or using the colour palette.
                # Don't need to search for colour bands when rendering in black.
                # Note that you can do custom black rendering using the colour palette.
                if not black:
                    # Work out which band the pixel colour falls into.
                    # Not a band is between colour boundaries.
                    # Find the first one that matches.
                    foundBand = False
                    belowBands = False
                    aboveBands = False
                    for b in range (0, useFulBoundaries - 1):
                        # Check if iterations greater than boundary iteration limit.
                        if self.iterations[row][col] > self.palette.colBoundaries[b].itLimit :
                            # Greater than limit; check less than or equal to next boundary limit.
                            if self.iterations[row][col] <= self.palette.colBoundaries[b+1].itLimit :
                                foundBand = True
                                break
                        else:
                            if b == 0 :
                                # Lower than first colour boundary, therefore below first band.
                                belowBands = True
                                break
                    # Check for above last boundary.
                    if not foundBand:
                        if self.iterations[row][col] > self.palette.colBoundaries[useFulBoundaries - 1].itLimit :
                            aboveBands = True

                    # Determine the pixel colour.
                    # Depends on whether we found iterations in or outside boundaries.
                    if foundBand:
                        pxRed, pxGreen, pxBlue = getColInRange(self.iterations[row][col], self.palette.colBoundaries[b], self.palette.colBoundaries[b+1])
                    elif belowBands:
                        pxRed = self.palette.colBoundaries[0].colRed
                        pxGreen = self.palette.colBoundaries[0].colGreen
                        pxBlue = self.palette.colBoundaries[0].colBlue
                    elif aboveBands:
                        pxRed = self.palette.colBoundaries[useFulBoundaries - 1].colRed
                        pxGreen = self.palette.colBoundaries[useFulBoundaries - 1].colGreen
                        pxBlue = self.palette.colBoundaries[useFulBoundaries - 1].colBlue
                else:
                    # Option to render just in black (and shades there of) selected.
                    # Don't need to check colour palette.
                    intensity = math.floor((self.iterations[row][col] - self.lowBin) / (self.maxIterations - self.lowBin) * 255)
                    pxRed = intensity
                    pxGreen = intensity
                    pxBlue = intensity

                # Update the image pixel colour.
                self.pilPic.putpixel((col, row), (pxRed, pxGreen, pxBlue))

        # Get the pixel data from the PIL image and update Gtk pixel buffer and Gtk Image.
        data = GLib.Bytes.new(self.pilPic.tobytes())
        pixbuf = GdkPixbuf.Pixbuf.new_from_bytes(data, GdkPixbuf.Colorspace.RGB, False, self.imageColours, self.imageWidth, self.imageHeight, self.imageWidth * 3)
        self.gtkPic.set_from_pixbuf(pixbuf)

# *******************************************
# Create main window, and launch.
# Window constructed from Glade definition file.
# *******************************************
builder = Gtk.Builder()
builder.add_from_file("chaos.glade")
builder.connect_signals(Handler())
win = builder.get_object("mainWindow")

mandle = Mandelbrot(win)
win.show_all()
Gtk.main()
