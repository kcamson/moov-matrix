import time
import board
import displayio
import gifio
from adafruit_matrixportal.matrixportal import MatrixPortal

matrixportal = MatrixPortal(
    status_neopixel=board.NEOPIXEL,
)

DISPLAY = matrixportal.display
# Setup the file as the bitmap data source
odg = gifio.OnDiskGif('/fireworks.gif')
start = time.monotonic()
next_delay = odg.next_frame() # Load the first frame
end = time.monotonic()
overhead = end - start

# Create a TileGrid to hold the bitmap
tile_grid = displayio.TileGrid(odg.bitmap, pixel_shader=displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565_SWAPPED))

# Create a Group to hold the TileGrid
group = displayio.Group()

# Add the TileGrid to the Group
group.append(tile_grid)

# Add the Group to the Display
DISPLAY.root_group = group

# Loop forever so you can enjoy your image
while True:
    time.sleep(max(0, next_delay - overhead))
    next_delay = odg.next_frame()