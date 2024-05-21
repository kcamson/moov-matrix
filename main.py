import time
import board
import displayio
import json
import gifio
from adafruit_matrixportal.network import Network
from adafruit_matrixportal.matrix import Matrix
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
matrixportal = Matrix()
display = matrixportal.display

# Root group for the leaderboard. Another group may temporarily replace this group to show gifs.
ROOT = displayio.Group(x=GLOBAL_X_OFFSET, y=GLOBAL_Y_OFFSET)
display.root_group = ROOT

NETWORK = Network(status_neopixel=board.NEOPIXEL, debug=True)
# NETWORK.connect()

def show_gif(gif:gifio.OnDiskGif, duration:float=1) -> None:
    """Show a gif on the display for a certain duration.

    Parameters
    ----------
    gif: gifio.OnDiskGif
        The gif to show.
    duration: float
        The duration to show the gif in seconds.
    """

    assert duration > 0, "Duration must be positive."
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

def build_color(red:int, green:int, blue:int) -> int:
    """RGB -> 16-bit color."""
    return (red << 16) + (green << 8) + blue

def create_label(text:str, font:bitmap_font, color:int=0xFFFFFF) -> adafruit_display_text.label.Label:
    """Creates a label."""
    return adafruit_display_text.label.Label(font, text=text, color=color)

def fetch_student_data_from_file(filename:str="/data.json") -> dict:
    """Fetches student data from a file.
    
    Parameters
    ----------
    filename: str
        The name of the file to fetch the student data from.

    Returns
    -------
    dict
        The student data (e.g. {"freshmen": 0, "sophomores": 0, "juniors": 0, "seniors": 0}).
    """
    try:
        with open(filename, "r") as f:
            data = json.load(f)
    except FileNotFoundError:
        data = {"freshmen": 0, "sophomores": 0, "juniors": 0, "seniors": 0}
        print("File not found. Using default data.")
    return data

def fetch_student_data(endpoint:str="https://fghs-matrix-z72fjkyoga-uc.a.run.app/") -> dict:
    """Fetches student data from the endpoint.
    
    Parameters
    ----------
    endpoint: str
        The endpoint to fetch the student data from.
    
    Returns
    -------
    dict
        The student data (e.g. {"freshmen": 0, "sophomores": 0, "juniors": 0, "seniors": 0}).
    """
    try:
        response = NETWORK.fetch_data(endpoint)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {"freshmen": 0, "sophomores": 0, "juniors": 0, "seniors": 0}
    return json.loads(response)

class ClassData:
    """All the data for a class. Currently seems like an over-abstraction but if more data is added, could be useful (e.g. class events, rally victories, etc.)"""
    def __init__(self, name:str, percentage:float=0) -> None:
        """
        Parameters
        ----------
        percentage: int
            The percentage of the class that is present.
        """
        self.name = name
        self.percentage = percentage
        self.celebrated = False
        self.group = None
        self.data_group = None

    def update(self, percentage:float) -> None:
        """Updates all of the data for the class.
        
        Parameters
        ----------
        percentage: float
            The new percentage of the class that is present.
        """
        self.percentage = percentage

        if self.data_group is not None:
            self.data_group[0].text = self.data_string
            self.data_group[0].color = self.data_color

    def create_group(self, x_offset:int, y_offset:int) -> displayio.Group:
        """Creates a group for the class.
        
        Parameters
        ----------
        x_offset: int
            The x offset of the group.
        y_offset: int
            The y offset of the group.
        
        Returns
        -------
        ClassGroup
            The group for the class.
        """
        # Create the group that contains the labels
        self.group = displayio.Group(x=x_offset, y=y_offset)

        # Create the group for the name label and append it to the main group
        label_group = displayio.Group(x=0, y=0)
        self.group.append(label_group)

        # Create the group for the data label and append it to the main group
        self.data_group = displayio.Group(x=int(GLOBAL_WIDTH/2.3), y=0)
        self.group.append(self.data_group)

        # Create the labels
        label = create_label(self.name, SMALL_FONT)
        label_group.append(label)

        data = create_label(self.data_string, SMALL_FONT, self.data_color)
        self.data_group.append(data)

        return self.group
    
    @property
    def data_string(self):
        return f"{self.percentage}%"
    
    @property
    def data_color(self):
        return build_color(255 - int(255 * (self.percentage / 100)), int(255 * (self.percentage / 100)), 0)
    
class StudentData:
    """All the data for the students. Contains all the data for each class. Again, seems like an over-abstraction but could be useful if some school-wide data is added."""
    def __init__(self) -> None:
        self.data = fetch_student_data_from_file()
        self.fre = ClassData("FSMN", self.data["freshmen"])
        self.sop = ClassData("SPHS", self.data["sophomores"])
        self.jun = ClassData("JNRS", self.data["juniors"])
        self.sen = ClassData("SNRS", self.data["seniors"])

        self.classes = [self.fre, self.sop, self.jun, self.sen]
    
    def update(self) -> None:
        """Updates all of the data for the students."""
        self.data = fetch_student_data_from_file()
        self.fre.update(self.data["freshmen"])
        self.sop.update(self.data["sophomores"])
        self.jun.update(self.data["juniors"])
        self.sen.update(self.data["seniors"])

def show_celebration(data_label:adafruit_display_text.label.Label) -> None:
    """Flash label colors and show a gif if a class has reached 100% attendance. Is blocking.
    
    Parameters
    ----------
    data_label: adafruit_display_text.label.Label
        The label to celebrate.
    """
    data_label.color = build_color(255, 0, 0)
    time.sleep(0.3)
    data_label.color = build_color(255, 127, 0)
    time.sleep(0.3)
    data_label.color = build_color(255, 255, 0)
    time.sleep(0.3)
    data_label.color = build_color(0, 255, 0)
    time.sleep(0.3)
    data_label.color = build_color(0, 0, 255)
    time.sleep(0.3)
    data_label.color = build_color(75, 0, 130)
    time.sleep(0.3)
    data_label.color = build_color(143, 0, 255)
    time.sleep(0.3)

    show_gif(FIREWORKS_GIF, duration=5)

student_data = StudentData()

# Create the groups for each class and append them to the root group
for class_data in student_data.classes:
    class_data.create_group(0, (len(ROOT)*GLOBAL_HEIGHT)//4)
    ROOT.append(class_data.group)

i = 0
while True:
    i = min(i + 4, 100)
    student_data.fre.update(i)
    for class_data in student_data.classes:
        if class_data.percentage == 100 and not class_data.celebrated:
            class_data.celebrated = True
            show_celebration(class_data.data_group[0])

    # student_data.update()
    time.sleep(0.2)
