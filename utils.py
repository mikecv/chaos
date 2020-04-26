#!/usr/bin/env python3

import gi
import math

# *******************************************
# Classes needs Gtk version 3.0.
# *******************************************
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# *******************************************
# Function to calculate colour in range.
# Given iteration count and low and high boundaries.
# *******************************************
def getColInRange(it, bLo, bHi):
    # Check that iterations are between boundaries.
    if ((it < bLo.itLimit) or (it > bHi.itLimit)):
        logger.debug("Iterations not between boundary iterations.")
    else:
        # Determine where in iteration range point is.
        # Note iterations always increasing.
        itRange = bHi.itLimit - bLo.itLimit
        ratio = (it - bLo.itLimit) / itRange

        # Apply range to colour limits for boundaries.
        # Note that colour limits can be increasing, decreasing, or the same.
        # Red
        redDiff = bHi.colRed - bLo.colRed
        if (redDiff == 0):
            colRed = bLo.colRed
        else:
            colRed = math.floor(bLo.colRed + (redDiff * ratio))
        # Green
        greenDiff = bHi.colGreen - bLo.colGreen
        if (greenDiff == 0):
            colGreen = bLo.colGreen
        else:
            colGreen = math.floor(bLo.colGreen + (greenDiff * ratio))
        # Blue
        blueDiff = bHi.colBlue - bLo.colBlue
        if (blueDiff == 0):
            colBlue = bLo.colBlue
        else:
            colBlue = math.floor(bLo.colBlue + (blueDiff * ratio))

    return colRed, colGreen, colBlue

# *******************************************
# Construct gtk.gdk.Color from components
# *******************************************
def conGdkCol(red, green, blue, alpha):
    return Gdk.RGBA(red / 255.0, green / 255.0, blue / 255.0, alpha / 255.0)

# *******************************************
# Function to parse object to dictionary items.
# *******************************************
def objToDict(obj):
    output = {}
    # Go through keys/items in object dictionary.
    for key, item in obj.__dict__.items():
        if isinstance(item, list):
            itemList = []
            for item in item:
                subItem = objToDict(item)
                itemList.append(subItem)
            output[key] = itemList
        else:
            output[key] = item
    # Return the object dictionary.
    return output

# *******************************************
# Function to return the sign of an unsigned int.
# *******************************************
def intSign(x):
    return (1-(x<=0))
