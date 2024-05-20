import time
import board
import terminalio
import displayio
from adafruit_matrixportal.matrixportal import MatrixPortal

matrixportal = MatrixPortal(
    status_neopixel=board.NEOPIXEL,
)

DISPLAY = matrixportal.display
# Setup the file as the bitmap data source
bitmap = displayio.OnDiskBitmap("/viking.bmp")
print(bitmap.width, bitmap.height)

# Create a TileGrid to hold the bitmap
tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)

# Create a Group to hold the TileGrid
group = displayio.Group()

# Add the TileGrid to the Group
group.append(tile_grid)

# Add the Group to the Display
DISPLAY.root_group = group

# Loop forever so you can enjoy your image
while True:
    pass