"""
********************************************************************************
Justin Lanan & Steven Shi
"Simulating Phagocytosis in Hexagonal Coordinates"
Group 6 - Final Project
Software Carpentry
Due: 12/19/2022

Main protocol does...
!!!
    Important Detail:
!!!!
********************************************************************************
"""

from PIL import Image
import math
import cv2
import os

class Board:
    def __init__(self, hex_diag, width, name, organisms):
        self.hex_diag, self.width, self.name, self.organisms = hex_diag, width, name, organisms
        self.height = self.get_height()
        self.midpoint = (math.floor(self.hex_diag / 2), 0)
        # Get max_hy and min_hy values indexed 0 to hex_diag
        self.hy_maxes = [math.floor(0.5 * (self.hex_diag - i)) for i in range(self.hex_diag + 1)]
        self.hy_mins = [math.ceil(-0.5 * i) for i in range(self.hex_diag + 1)]
        # Get max_x internal quadrant dimensions for defining a hex
        self.quad_max_xs = [(round(self.width / 2 - j * 1 / 3 ** 0.5)) for j in range(round(self.height / 2))]
        self.px_max, self.py_max = self.get_pxy_max()
        self.out_of_bounds = self.get_oob()
        self.img = self.blank()
        if organisms is None:
            pass
        else:
            for org in self.organisms:
                for hxhy in org.hxhy_list:
                    if hxhy:
                        self.paint_pixels_of_hex(org.rgb, hxhy)

    def get_height(self):
        # Get hexagon pixel height as float
        height = self.width / 2 * 3 ** 0.5
        return height

    def get_pxy_max(self):
        # Calculate max pixel coordinates on the board via hex coordinate (hex_diag, 0)
        hx, hy = self.hex_diag, 0
        shift_x = math.floor(self.width / 2 + self.width / 2 * (hx * 3 / 2))
        shift_y = math.floor(self.height / 2 + self.width / 2 * (hx / 2 * 3 ** 0.5 + hy * 3 ** 0.5))
        px_max = shift_x + math.ceil(self.width / 2)
        py_max = shift_y + math.ceil(self.height / 2)
        return px_max, py_max

    def get_oob(self):
        # Create list of (hx,hy) tuples that define the first layer that is out of bounds
        # Have side boundaries include the corner points
        sides = []
        for hy in range(-1, self.hy_maxes[0] + 2):
            sides.append((-1, hy))
            sides.append((self.hex_diag + 1, -1 * hy))
        top_and_bot = []
        for hx in range(self.hex_diag + 1):
            top_and_bot.append((hx, self.hy_maxes[hx] + 1))
            top_and_bot.append((hx, self.hy_mins[hx] - 1))
        # Dump into a single list of tuples defining the out-of-bounds layer
        return [*sides, *top_and_bot]

    def blank(self):
        # Make white rectangular backdrop
        return Image.new(mode="RGB", size=(self.px_max, self.py_max), color=(255, 255, 255))

    def paint_pixels_of_hex(self, rgb, hxhy):
        shift_x = math.floor(self.width / 2 + self.width / 2 * (hxhy[0] * 3 / 2))
        shift_y = math.floor(self.height / 2 + self.width / 2 * (hxhy[0] / 2 * 3 ** 0.5 + hxhy[1] * 3 ** 0.5))
        for j, item in enumerate(self.quad_max_xs):
            for i in range(item):
                self.img.putpixel((shift_x + i, shift_y + j), rgb)
                self.img.putpixel((shift_x - i, shift_y + j), rgb)
                self.img.putpixel((shift_x - i, shift_y - j), rgb)
                self.img.putpixel((shift_x + i, shift_y - j), rgb)

    def save(self):
        # Save out the image to local folder
        if not self.name.endswith(".png"):
            self.name += ".png"
        self.img.save(self.name)


class Ciliate:
    def __init__(self, rgb, hxhy_list):
        self.rgb = rgb
        self.hxhy_list = hxhy_list


class Amoeba:
    def __init__(self, rgb, hxhy_list):
        self.rgb = rgb
        self.hxhy_list = hxhy_list


class Neighbors2Hex:
    def __init__(self, hxhy, brd):
        self.hxhy, self.board = hxhy, brd
        self.neighbors = self.get_neighs()
        self.up_left, self.up, self.up_right, self.low_right, self.down, self.low_left = (
            self.neighbors[0], self.neighbors[1], self.neighbors[2],
            self.neighbors[3], self.neighbors[4], self.neighbors[5])

    def get_neighs(self):
        hxhy_up_left = (self.hxhy[0] - 1, self.hxhy[1])
        if hxhy_up_left in self.board.out_of_bounds:
            hxhy_up_left = None
        hxhy_up = (self.hxhy[0], self.hxhy[1] - 1)
        if hxhy_up in self.board.out_of_bounds:
            hxhy_up = None
        hxhy_up_right = (self.hxhy[0] + 1, self.hxhy[1] - 1)
        if hxhy_up_right in self.board.out_of_bounds:
            hxhy_up_right = None
        hxhy_low_right = (self.hxhy[0] + 1, self.hxhy[1])
        if hxhy_low_right in self.board.out_of_bounds:
            hxhy_low_right = None
        hxhy_down = (self.hxhy[0], self.hxhy[1] + 1)
        if hxhy_down in self.board.out_of_bounds:
            hxhy_down = None
        hxhy_low_left = (self.hxhy[0] - 1, self.hxhy[1] + 1)
        if hxhy_low_left in self.board.out_of_bounds:
            hxhy_low_left = None
        return [hxhy_up_left, hxhy_up, hxhy_up_right, hxhy_low_right, hxhy_down, hxhy_low_left]


def initialize_4_ciliates(brd):
    # Lay 4 ciliates, one in each corner, start with defined colors and center points
    rgb1, rgb2, rgb3, rgb4 = (0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)
    hxhy1_o = (1, 0)                                       # upper left
    hxhy2_o = (brd.hex_diag - 1, brd.hy_mins[-3])          # upper right
    hxhy3_o = (1, brd.hy_maxes[2])                         # lower left
    hxhy4_o = (brd.hex_diag - 1, 0)                        # lower right
    # Get neighbors of the center points
    neighs1, neighs2, neighs3, neighs4 = (
        Neighbors2Hex(hxhy1_o, brd), Neighbors2Hex(hxhy2_o, brd),
        Neighbors2Hex(hxhy3_o, brd), Neighbors2Hex(hxhy4_o, brd))
    hxhy1 = [neighs1.up_left, hxhy1_o, neighs1.low_right]  # upper left
    hxhy2 = [neighs2.low_left, hxhy2_o, neighs2.up_right]  # upper right
    hxhy3 = [neighs3.low_left, hxhy3_o, neighs3.up_right]  # lower left
    hxhy4 = [neighs4.up_left, hxhy4_o, neighs4.low_right]  # lower right
    return [Ciliate(rgb1, hxhy1), Ciliate(rgb2, hxhy2), Ciliate(rgb3, hxhy3), Ciliate(rgb4, hxhy4)]


def initialize_amoeba(radius, brd):
    # Center of amoeba at center of board
    rgb = (25, 255, 255)
    hxhy = [brd.midpoint]
    # use rotation method to make concentric circles
    for r in range(1, radius + 1):
        for hy in range(0, -1 * r - 1, -1):
            vect0 = (r, hy)
            vect1 = (r + hy, -1 * r)
            vect2 = (hy, -1 * r - hy)
            vect3 = (-1 * r, -1 * hy)
            vect4 = (-1 * r - hy, r)
            vect5 = (-1 * hy, r + hy)
            hxhy.append((vect0[0] + hxhy[0][0], vect0[1]))
            hxhy.append((vect1[0] + hxhy[0][0], vect1[1]))
            hxhy.append((vect2[0] + hxhy[0][0], vect2[1]))
            hxhy.append((vect3[0] + hxhy[0][0], vect3[1]))
            hxhy.append((vect4[0] + hxhy[0][0], vect4[1]))
            hxhy.append((vect5[0] + hxhy[0][0], vect5[1]))
    return Amoeba(rgb, hxhy)


if __name__ == "__main__":
    # Define the board by entering number of hexagons across the diagonal and the pixel width of each hexagon.
    # Knobs: recommend 120, 36, 10
    hex_count = 120
    pixel_width_of_hex = 36
    amoeba_radius = 10

    # Just to show syntax for a blank board
    image_name = "Blank Hex Board"
    board = Board(hex_count, pixel_width_of_hex, image_name, organisms=None)
    board.save()

    # Get initial list of organism objects
    collection_of_organisms = initialize_4_ciliates(board)
    collection_of_organisms.append(initialize_amoeba(amoeba_radius, board))
    image_name = "4 Ciliates and Amoeba"
    board = Board(hex_count, pixel_width_of_hex, image_name, collection_of_organisms)
    board.save()
    # Use OpenCv to combine the images into a movie
    image_folder = 'images'
    video_name = 'video.avi'

    images = [img for img in os.listdirt(image_folder) if img.endswith(".png")]
    frame = cv2.imread(os.path.join(image_folder,images[0]))
    height,width,layers = frame.shape

    Video = cv2.VideoWriter(video_name,0,1,(width,height))

    for image in images:
        video.write(cv2.imread(os.path.join(image_folder,image)))

    cv2. destroyAllWindows()
    video.release()