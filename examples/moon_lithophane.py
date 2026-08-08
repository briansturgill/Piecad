"""
Make a lithophane from a NASA photo of both sides of the moon.
"""

from piecad import *

if __name__ == "__main__":
    o = lithophane("moon_lithophane.jpg", width_mm=250)
    o = o.rotate((90, 0, 45))
    save("moon_lithophane.obj", o)
    view(o)
