import time
import board
import displayio
import json
import gifio
from adafruit_matrixportal.matrixportal import MatrixPortal
from adafruit_bitmap_font import bitmap_font
import adafruit_display_text.label

# Offsets for root group. This changes with font.
GLOBAL_X_OFFSET = 0
GLOBAL_Y_OFFSET = 3

# Dimensions of the display
GLOBAL_WIDTH = 64
GLOBAL_HEIGHT = 32

# Load the font (currently only font being used)
SMALL_FONT = bitmap_font.load_font('/fonts/6x10.bdf')
SMALL_FONT.load_glyphs('0123456789:/.%')

# Load all gifs. Trying to load a gif during runtime throws a MemoryError.
FIREWORKS_GIF = gifio.OnDiskGif('fireworks.gif')

# Set up the matrix portal and display
matrixportal = MatrixPortal(
    status_neopixel=board.NEOPIXEL,
)
display = matrixportal.display

# Root group for the leaderboard. Another group may temporarily replace this group to show gifs.
ROOT = displayio.Group(x=GLOBAL_X_OFFSET, y=GLOBAL_Y_OFFSET)
display.root_group = ROOT

# 
def show_gif(gif:gifio.OnDiskGif, duration:float=0):
    # Code from https://docs.circuitpython.org/en/latest/shared-bindings/gifio/index.html#gifio.OnDiskGif to show a gif
    start = time.monotonic()
    next_delay = gif.next_frame()
    end = time.monotonic()
    overhead = end - start
    tile_grid = displayio.TileGrid(gif.bitmap, pixel_shader=displayio.ColorConverter(input_colorspace=displayio.Colorspace.RGB565_SWAPPED))
    
    # Temporarily set the root group to the gif group
    gif_group = displayio.Group()
    gif_group.append(tile_grid)
    display.root_group = gif_group

    # Show the gif for the duration
    for _ in range(int(duration/next_delay)):
        time.sleep(max(0, next_delay - overhead))
        next_delay = gif.next_frame()
    
    # Reset the root group to the leaderboard
    display.root_group = ROOT

def build_color(red, green, blue):
    return (red << 16) + (green << 8) + blue

def create_label(text, font, color=0xFFFFFF):
    return adafruit_display_text.label.Label(font, text=text, color=color)

class ClassGroup:
    # A displayio Group that splits itself down the middle. Displays label to the left and data to the right.
    def __init__(self, root, label:str, data:str):
        self.root = root
        num_groups = len(root)
        self.group = displayio.Group(x=0, y=(GLOBAL_HEIGHT*num_groups//4))
        self.root.append(self.group)
        self.label_group = displayio.Group(x=0, y=0)
        self.group.append(self.label_group)
        self.data_group = displayio.Group(x=int(GLOBAL_WIDTH/2.3), y=0)
        self.group.append(self.data_group)
        self.label = create_label(label, SMALL_FONT)
        self.data = create_label(data, SMALL_FONT)
        self.label_group.append(self.label)
        self.data_group.append(self.data)

    def update(self, data:str, color:int=0xFFFFFF):
        self.data.text = data
        self.data.color = color

fresh_group = ClassGroup(ROOT, "FSMN", "0/0")
soph_group = ClassGroup(ROOT, "SPHS", "0/0")
jun_group = ClassGroup(ROOT, "JNRS", "0/0")
sen_group = ClassGroup(ROOT, "SNRS", "0/0")

def fetch_student_data():
    with open("/data.json", "r") as f:
        data = json.load(f)
    return data

class ClassData:
    def __init__(self, tapped_in=0, total_students=0):
        self.tapped_in = tapped_in
        self.total_students = total_students

    def update(self, tapped_in, total_students):
        self.tapped_in = tapped_in
        self.total_students = total_students
    
    @property
    def percentage(self):
        return self.tapped_in / self.total_students * 100
    
    def get_data_string(self):
        return f"{self.percentage}%"
    
    def get_data_color(self):
        return build_color(255 - int(255 * (self.percentage / 100)), int(255 * (self.percentage / 100)), 0)
    
class StudentData:
    def __init__(self):
        self.data = fetch_student_data()
        self.fresh = ClassData(**self.data["freshmen"])
        self.soph = ClassData(**self.data["sophomores"])
        self.jun = ClassData(**self.data["juniors"])
        self.sen = ClassData(**self.data["seniors"])
    
    def update(self):
        self.data = fetch_student_data()
        self.fresh.update(**self.data["freshmen"])
        self.soph.update(**self.data["sophomores"])
        self.jun.update(**self.data["juniors"])
        self.sen.update(**self.data["seniors"])

student_data = StudentData()
i = 0
celebrated = False
while True:
    i = min(i + 5, 500)
    student_data.fresh.update(i, 500)
    if i == 500 and not celebrated:
        # Update fresh_group with rainbow colors and then show a gif
        fresh_group.update(student_data.fresh.get_data_string(), build_color(255, 0, 0))
        time.sleep(0.3)
        fresh_group.update(student_data.fresh.get_data_string(), build_color(255, 127, 0))
        time.sleep(0.3)
        fresh_group.update(student_data.fresh.get_data_string(), build_color(255, 255, 0))
        time.sleep(0.3)
        fresh_group.update(student_data.fresh.get_data_string(), build_color(0, 255, 0))
        time.sleep(0.3)
        fresh_group.update(student_data.fresh.get_data_string(), build_color(0, 0, 255))
        time.sleep(0.3)
        fresh_group.update(student_data.fresh.get_data_string(), build_color(75, 0, 130))
        time.sleep(0.3)
        fresh_group.update(student_data.fresh.get_data_string(), build_color(143, 0, 255))
        time.sleep(0.3)

        show_gif(FIREWORKS_GIF, duration=5)
        celebrated = True

    fresh_group.update(student_data.fresh.get_data_string(), student_data.fresh.get_data_color())
    soph_group.update(student_data.soph.get_data_string(), student_data.soph.get_data_color())
    jun_group.update(student_data.jun.get_data_string(), student_data.jun.get_data_color())
    sen_group.update(student_data.sen.get_data_string(), student_data.sen.get_data_color())
    # student_data.update()
    time.sleep(0.2)
