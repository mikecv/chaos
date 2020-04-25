#!/usr/bin/env python3

import threading
import math
import cmath

# *******************************************
# Perform inmage calculation thread.
# *******************************************
class imageCalc(threading.Thread):

    # *******************************************
    # Thread initialisation.
    # Argument includes the main Mandlebrot class,
    # and row and column limit coupletes.
    # For complete image coupletes should be (0, width-1) (0, height-1)
    # *******************************************
    def __init__(self, threadID, threadName, logger, chaos, rowRange, colRange):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.threadName = threadName
        self.logger = logger
        self.chaos = chaos
        self.rowRange = rowRange
        self.colRange = colRange

        # Get pixel increment size.
        self.inc = self.chaos.pxSize

        self.logger.debug("Calculating image rangers, ROWS : ({0:d}, {1:d}), COLUMNS : ({2:d}, {3:d})".format(self.rowRange[0], self.rowRange[1], self.colRange[0], self.colRange[1]))
        self.logger.debug("Image centre location, REAL : {0:f}, IMAGINARY : , {1:f}".format(self.chaos.centreReal, self.chaos.centreImag))

        # Determine start point (top left) for box to calculate.
        self.calcStartX = self.chaos.centreReal - (((self.chaos.imageWidth / 2.0) - self.colRange[0]) * self.inc)
        self.calcStartY = self.chaos.centreImag + (((self.chaos.imageHeight / 2.0) - self.rowRange[0]) * self.inc)
        self.logger.debug("Calculating image at start position, REAL : {0:f}, IMAGINARY : {1:f}".format(self.calcStartX, self.calcStartY))

    # *******************************************
    # Run method called when thread started.
    # *******************************************
    def run(self):
        # Initialise complex value of first pixel point.
        pt = complex(self.calcStartX, self.calcStartY)

        # Calculate max iterations for all pixels.
        for row in range (self.rowRange[0], self.rowRange[1]):
            for col in range (self.colRange[0], self.colRange[1]):
                # Initialise divergence to false; keep looping until divergence confirmed.
                diverges = False
                # Initialise iteration count.
                numIterations = 1
                # Initialise the function result of the Mandelbrot function.
                pxFn = complex(0.0, 0.0)

                # Keep iterating until function diverges.
                while ((diverges == False) & (numIterations < self.chaos.maxIterations)):
                    # Mandelbrot function is Fn+1 = Fn^2 + pt
                    pxFn = (pxFn * pxFn) + pt
                    # Check for divergence towards infinity.
                    # Divergence guaranteed if modulus of Fn is >= 2.
                    modFn2 = cmath.polar(pxFn)[0]
                    if (modFn2 >= 2.0):
                        diverges = True
                    else:
                        numIterations += 1

                # Divergence so far is overstated or assured divergence.
                # Can calculate fractional divergence for higher definition.
                # Fractional divergence can be approximated as mu = log (log(|Z(n)|)) / log(2)
                modFn = cmath.polar(pxFn)[0]
                if (modFn > math.e):
                    muLog = math.log(math.log(cmath.polar(pxFn)[0])) / math.log(2.0)
                else:
                    muLog = 0
                mu = float(numIterations) + 1 - muLog

                # Limit fractional divergence to maximum iterations.
                if (mu > self.chaos.maxIterations):
                    mu = self.chaos.maxIterations

                # Update number of iterations in the image iterations array.
                self.chaos.iterations[row][col] = mu

                # Increment point to next point in row.
                pt = pt + complex(self.inc, 0.0)

            # Increment point to start of next row.
            pt = pt - complex(0.0, self.inc)
            pt = complex(self.calcStartX, pt.imag)
