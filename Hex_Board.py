"""
********************************************************************************
Justin Lanan & Steven Shi
"Hexagonal Microbes"
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
import os
import shutil
import random
import cv2
import os
import numpy as np
import glob

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
        if self.organisms is None:
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
    def __init__(self, rgb, hxhy_list, brd):
        self.rgb = rgb
        self.hxhy_list = hxhy_list
        self.brd = brd
        self.moved_hxhy_list = self.random_move()

    def random_move(self):
        # 0: forward, 1: backward, 2: rotate +60, 3: rotate -60
        move_type = random.choice([0, 0, 0, 0, 0, 0, 1, 1, 2, 3])
        orientation = self.get_orientation()
        hypothetical_new_hxhy_list = self.hypothetical_new_hxhy(move_type, orientation)
        is_valid = self.is_valid_move(hypothetical_new_hxhy_list)
        if is_valid:
            return hypothetical_new_hxhy_list
        else:
            return self.hxhy_list

    def get_orientation(self):
        # Head is 0: upper left, 1: up, 2: upper right, 3: lower right, 4: down, 5: lower left
        if self.hxhy_list[0] == Neighbors2Hex(self.hxhy_list[1], self.brd).up_left:
            return 0
        elif self.hxhy_list[0] == Neighbors2Hex(self.hxhy_list[1], self.brd).up:
            return 1
        elif self.hxhy_list[0] == Neighbors2Hex(self.hxhy_list[1], self.brd).up_right:
            return 2
        elif self.hxhy_list[0] == Neighbors2Hex(self.hxhy_list[1], self.brd).low_right:
            return 3
        elif self.hxhy_list[0] == Neighbors2Hex(self.hxhy_list[1], self.brd).down:
            return 4
        elif self.hxhy_list[0] == Neighbors2Hex(self.hxhy_list[1], self.brd).low_left:
            return 5

    def hypothetical_new_hxhy(self, move_type, orientation):
        # Get vector from middle to head of ciliate
        vector_1to0 = (self.hxhy_list[0][0] - self.hxhy_list[1][0], self.hxhy_list[0][1] - self.hxhy_list[1][1])
        head_will_be_at, mid_will_be_at, tail_will_be_at = (), (), ()
        # Based on that vector, the move type, and current orientation, get hypothetical new coordinates
        if move_type == 0:  # Forwards
            head_will_be_at = (self.hxhy_list[0][0] + vector_1to0[0], self.hxhy_list[0][1] + vector_1to0[1])
            mid_will_be_at = (self.hxhy_list[1][0] + vector_1to0[0], self.hxhy_list[1][1] + vector_1to0[1])
            tail_will_be_at = (self.hxhy_list[2][0] + vector_1to0[0], self.hxhy_list[2][1] + vector_1to0[1])
        elif move_type == 1:  # Backwards
            head_will_be_at = (self.hxhy_list[0][0] - vector_1to0[0], self.hxhy_list[0][1] - vector_1to0[1])
            mid_will_be_at = (self.hxhy_list[1][0] - vector_1to0[0], self.hxhy_list[1][1] - vector_1to0[1])
            tail_will_be_at = (self.hxhy_list[2][0] - vector_1to0[0], self.hxhy_list[2][1] - vector_1to0[1])
        elif move_type == 2:  # Rotate +60
            mid_will_be_at = self.hxhy_list[1]
            if orientation == 0:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).low_left
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up_right
            elif orientation == 1:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up_left
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).low_right
            elif orientation == 2:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).down
            elif orientation == 3:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up_right
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).low_left
            elif orientation == 4:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).low_right
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up_left
            elif orientation == 5:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).down
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up
        elif move_type == 3:  # Rotate -60
            mid_will_be_at = self.hxhy_list[1]
            if orientation == 0:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).down
            elif orientation == 1:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up_right
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).low_left
            elif orientation == 2:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).low_right
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up_left
            elif orientation == 3:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).down
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up
            elif orientation == 4:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).low_left
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up_right
            elif orientation == 5:
                head_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).up_left
                tail_will_be_at = Neighbors2Hex(self.hxhy_list[1], self.brd).low_right
        return [head_will_be_at, mid_will_be_at, tail_will_be_at]

    def is_valid_move(self, new_hxhy_list):
        big_list = self.get_list_of_everything_besides_this_ciliate()
        for hxhy in new_hxhy_list:
            if hxhy in big_list:
                return False
        return True

    def get_list_of_everything_besides_this_ciliate(self):
        big_list_of_hxhy = self.brd.out_of_bounds
        if self.brd.organisms is not None:
            all_organisms = self.brd.organisms
            for org in all_organisms:
                big_list_of_hxhy.extend(org.hxhy_list)
            for hxhy in self.hxhy_list:
                if hxhy in big_list_of_hxhy:
                    big_list_of_hxhy.remove(hxhy)
        return big_list_of_hxhy


class Amoeba:
    def __init__(self, rgb, hxhy_list, brd):
        self.rgb = rgb
        self.hxhy_list = hxhy_list
        self.brd = brd
        self.perimeter_hxhy_list = self.get_perimeter()
        self.fingertips_hxhy_list, self.necks_hxhy_list, self.base_hxhy_list = self.get_fngr_neck_base()
        self.reduced_p_hxhy_list = self.get_reduced_perimeter()
        self.moved_hxhy_list = self.random_move()

    def get_perimeter(self):
        perimeter_hxhy_list = []
        for hxhy in self.hxhy_list:
            for neigh_hxhy in Neighbors2Hex(hxhy, self.brd).neighbors:
                if neigh_hxhy not in self.hxhy_list:
                    perimeter_hxhy_list.append(hxhy)
                    break
        return perimeter_hxhy_list

    def get_fingertips(self):
        # Any perimeter hexagons that only have one self neighbor are fingertips.
        fingertips = []
        for hxhy in self.hxhy_list:
            neigh_count = 0
            for neigh_hxhy in Neighbors2Hex(hxhy, self.brd).neighbors:
                if neigh_hxhy in self.hxhy_list:
                    neigh_count += 1
            if neigh_count == 1:
                fingertips.append(hxhy)
        return fingertips

    def get_fngr_neck_base(self):
        # Scan perimeter hexagons to see if they are fingertips, neck pieces, or the bases of necks
        fingertips, necks, bases = [], [], []
        for hxhy in self.perimeter_hxhy_list:
            p_neigh_count = 0  # peripheral neighbors
            b_neigh_count = 0  # body neighbors
            for neigh_hxhy in Neighbors2Hex(hxhy, self.brd).neighbors:
                if neigh_hxhy in self.perimeter_hxhy_list:
                    p_neigh_count += 1
                if neigh_hxhy not in self.perimeter_hxhy_list and neigh_hxhy in self.hxhy_list:
                    b_neigh_count += 1
            fingertips, necks, bases = self.append_fngr_neck_base(
                hxhy, fingertips, necks, bases, p_neigh_count, b_neigh_count)
        return fingertips, necks, bases

    def append_fngr_neck_base(self, hxhy, fingertips, necks, bases, p_neigh_count, b_neigh_count):
        # Analyze neighbor counts (peripheral and body) to cover all possible morphologies and append accordingly.
        if p_neigh_count == 1 and b_neigh_count == 0:
            fingertips.append(hxhy)
        elif p_neigh_count == 2 and b_neigh_count == 0:
            # Can be a link in a skinny (neck)
            # Can be a wart on a wall (pass)
            is_wart = self.test_is_wart(hxhy)
            if not is_wart:
                necks.append(hxhy)
        elif p_neigh_count == 3 and b_neigh_count == 0:
            # Can be in the crux of a 'Y' (pass)
            # Can be (base)
            is_crux_of_y = self.test_is_crux_of_y(hxhy)
            if not is_crux_of_y:
                bases.append(hxhy)
        elif p_neigh_count == 3 and b_neigh_count == 1:
            # Can be mid of a side near a corner (pass)
            # Can be (base)
            is_3_to_1_base = self.test_is_3_to_1(hxhy)
            if is_3_to_1_base:
                bases.append(hxhy)
        elif p_neigh_count == 4 and b_neigh_count == 0:
            # Can be the center of a dog bone (base)
            # Can be the top stem piece of a mushroom (3-to-1) (base)
            # or the middle-edge piece of a small triangle (pass)
            is_dog_bone = self.test_is_dog_bone(hxhy)
            is_3_to_1_base = self.test_is_3_to_1(hxhy)
            if is_dog_bone:
                necks.append(hxhy)
            elif is_3_to_1_base:
                bases.append(hxhy)
        return fingertips, necks, bases

    def test_is_wart(self, hxhy):
        # The two neighbors of a wart are right next to each other.
        indexes = []
        for i, neigh_hxhy in enumerate(Neighbors2Hex(hxhy, self.brd).neighbors):
            if neigh_hxhy in self.hxhy_list:
                indexes.append(i)
        if abs(indexes[0] - indexes[1]) == 1 or abs(indexes[0] - indexes[1]) == 5:
            return True
        return False

    def test_is_crux_of_y(self, hxhy):
        # The three neighbors of a Y-crux are all right next to each other.
        indexes = []
        for i, neigh_hxhy in enumerate(Neighbors2Hex(hxhy, self.brd).neighbors):
            if neigh_hxhy in self.hxhy_list:
                indexes.append(i)
        diff1 = abs(indexes[0] - indexes[1])
        diff2 = abs(indexes[1] - indexes[2])
        if diff1 == 1 or diff1 == 5:
            if diff2 == 1 or diff2 == 5:
                return True
        return False

    def test_is_3_to_1(self, hxhy):
        # The 4 neighbors of a 3-to-1 base have a -0-1-2-gap-4-gap- pattern. Easier to index the gaps instead.
        indexes = []
        for i, neigh_hxhy in enumerate(Neighbors2Hex(hxhy, self.brd).neighbors):
            if neigh_hxhy not in self.hxhy_list:
                indexes.append(i)
        if abs(indexes[0] - indexes[1]) == 2 or abs(indexes[0] - indexes[1]) == 4:
            return True
        return False

    def test_is_dog_bone(self, hxhy):
        # The 4 neighbors of a dog bone base have a -0-1-gap-3-4-gap- pattern. Easier to index the gaps instead.
        indexes = []
        for i, neigh_hxhy in enumerate(Neighbors2Hex(hxhy, self.brd).neighbors):
            if neigh_hxhy not in self.hxhy_list:
                indexes.append(i)
        if abs(indexes[0] - indexes[1]) == 3:
            return True
        return False

    def get_reduced_perimeter(self):
        # get perimeter list but with narrow points removed. Leave the fingertips in the list.
        reduced_perimeter_hxhy_list = self.perimeter_hxhy_list.copy()
        for hxhy in self.perimeter_hxhy_list:
            # Keep the meat touchers that are not neck bases. Keep the fingertips. Delete the rest of the necks.
            if hxhy in self.necks_hxhy_list or hxhy in self.base_hxhy_list:
                reduced_perimeter_hxhy_list.remove(hxhy)
        return reduced_perimeter_hxhy_list

    def random_move(self):
        is_valid, hex_to_add, hex_to_remove = False, (0, 0), (0, 0)
        while not is_valid:
            # Randomly select from the reduced perimeter list for the move
            hex_chosen = self.perimeter_hxhy_list[random.randint(0, len(self.perimeter_hxhy_list) - 1)]
            # Choose random non-self neighbor to that hexagon to lay as new
            hex_to_add = self.get_added_hex(hex_chosen)
            if hex_to_add == (-1, 0):
                continue
            # Find the farthest hex in the amoeba to be removed
            hex_to_remove = self.get_farthest_perimeter_hex(hex_to_add)
            # Check that the hex to add won't land out of bounds or on another organism
            is_valid = self.is_valid_move(hex_to_add)
            if not is_valid:
                print('Invalid move, trying again...')
        hypothetical_new_hxhy_list = self.hxhy_list.copy()
        hypothetical_new_hxhy_list.append(hex_to_add)
        hypothetical_new_hxhy_list.remove(hex_to_remove)
        return hypothetical_new_hxhy_list

    def get_added_hex(self, hxhy):
        # From this self-perimeter hex, find empty neighbors. Check that these empty neighbors are not in a
        # "base" position (dogbone, 3_to_1, non-crux of Y, non-wart) based on their number of self-perimeter neighbors.
        empty_neighbors = []
        for neigh_hxhy in Neighbors2Hex(hxhy, self.brd).neighbors:
            if neigh_hxhy not in self.hxhy_list:
                p_neigh_count = 0
                for neigh_neigh_hxhy in Neighbors2Hex(neigh_hxhy, self.brd).neighbors:
                    if neigh_neigh_hxhy in self.perimeter_hxhy_list:
                        p_neigh_count += 1
                if p_neigh_count == 2:
                    # Could create a wart or a neck
                    creates_wart = self.test_is_wart(neigh_hxhy)
                    if creates_wart:
                        empty_neighbors.append(neigh_hxhy)
                elif p_neigh_count == 3:
                    # Could fill in the crux-of-a-Y or create a base
                    fills_in_crux = self.test_is_crux_of_y(neigh_hxhy)
                    if fills_in_crux:
                        empty_neighbors.append(neigh_hxhy)
                elif p_neigh_count == 4:
                    # Could create a dogbone or 3_to_1 base scenario and should be skipped.
                    creates_dogbone = self.test_is_dog_bone(neigh_hxhy)
                    creates_3_to_1 = self.test_is_dog_bone(neigh_hxhy)
                    if not creates_dogbone and not creates_3_to_1:
                        empty_neighbors.append(neigh_hxhy)
                else:
                    empty_neighbors.append(neigh_hxhy)
        # If empty_neighbors is empty then the chosen hex doesn't have empty neighbors that are valid moves.
        # Just send it off the board to (-1, 0) to be caught by the is_valid checker.
        if len(empty_neighbors) == 0:
            invalid_point = (-1, 0)
            return invalid_point
        return random.choice(empty_neighbors)

    def get_farthest_perimeter_hex(self, center_hex):
        # Keep checking concentric rings for self.reduced_perimeter coordinates until none are found.
        # The largest ring that still has reduced_perimeter coordinates should choose one at random if more than one,
        # but should not choose a fingertip if it's a tie. This will help keep the amoeba elongated.
        rings_list_of_lists, ring_list, refined_ring_list = [], [], []
        initialized, radius = False, 2
        while not initialized:
            # Initialize first ring to start the while loop
            raw_ring_list, ring_list = get_ring(center_hex, radius), []
            for hxhy in raw_ring_list:
                if hxhy in self.reduced_p_hxhy_list:
                    ring_list.append(hxhy)
            if len(ring_list) == 0:
                radius += 1
                continue
            initialized = True

        # Search larger and larger rings for self perimeter hexagons until none show up
        while len(ring_list) > 0:
            rings_list_of_lists.append(ring_list)
            # Reinitialize to a bigger ring
            ring_list, radius = [], radius + 1
            raw_ring_list = get_ring(center_hex, radius)
            for hxhy in raw_ring_list:
                if hxhy in self.reduced_p_hxhy_list:
                    ring_list.append(hxhy)

        # Randomly select from the outer half of the ring set for recruitment.
        index_1_of_2 = math.ceil(1 / 2 * (len(rings_list_of_lists) - 1))
        index_2_of_2 = len(rings_list_of_lists) - 1
        index = random.choice(range(index_1_of_2, index_2_of_2 + 1))
        outer_ring_list = rings_list_of_lists[index].copy()

        # Remove fingertips from selection if non-fingertips to choose from
        fngr_count = 0
        if len(outer_ring_list) > 1:
            for hxhy in outer_ring_list:
                if hxhy in self.fingertips_hxhy_list:
                    fngr_count += 1
            if fngr_count == len(outer_ring_list):
                for hxhy in outer_ring_list:
                    refined_ring_list.append(hxhy)
            else:
                for hxhy in outer_ring_list:
                    if hxhy not in self.fingertips_hxhy_list:
                        refined_ring_list.append(hxhy)
        else:
            refined_ring_list.extend(outer_ring_list)
        return random.choice(refined_ring_list)

    def is_valid_move(self, hxhy):
        big_list = self.get_list_of_everything_besides_the_amoeba()
        if hxhy in big_list:
            return False
        return True

    def get_list_of_everything_besides_the_amoeba(self):
        # Put the out of bounds and the ciliates in a list. Amoeba is indexed last in organisms list.
        big_list_of_hxhy = self.brd.out_of_bounds
        if self.brd.organisms is not None:
            all_organisms = self.brd.organisms
            for i, org in enumerate(all_organisms):
                if i < len(all_organisms) - 1:
                    big_list_of_hxhy.extend(org.hxhy_list)
        return big_list_of_hxhy


class Neighbors2Hex:
    def __init__(self, hxhy, brd):
        self.hxhy, self.board = hxhy, brd
        self.neighbors = self.get_neighs()
        self.up_left, self.up, self.up_right, self.low_right, self.down, self.low_left = (
            self.neighbors[0], self.neighbors[1], self.neighbors[2],
            self.neighbors[3], self.neighbors[4], self.neighbors[5])

    def get_neighs(self):
        hxhy_up_left = (self.hxhy[0] - 1, self.hxhy[1])
        hxhy_up = (self.hxhy[0], self.hxhy[1] - 1)
        hxhy_up_right = (self.hxhy[0] + 1, self.hxhy[1] - 1)
        hxhy_low_right = (self.hxhy[0] + 1, self.hxhy[1])
        hxhy_down = (self.hxhy[0], self.hxhy[1] + 1)
        hxhy_low_left = (self.hxhy[0] - 1, self.hxhy[1] + 1)
        return [hxhy_up_left, hxhy_up, hxhy_up_right, hxhy_low_right, hxhy_down, hxhy_low_left]


def get_ring(hxhy, r):
    # Use rotation method to make concentric hex rings
    ring_list = []
    for hy in range(0, -1 * r, -1):
        vect0 = (r, hy)
        vect1 = (r + hy, -1 * r)
        vect2 = (hy, -1 * r - hy)
        vect3 = (-1 * r, -1 * hy)
        vect4 = (-1 * r - hy, r)
        vect5 = (-1 * hy, r + hy)
        ring_list.append((vect0[0] + hxhy[0], vect0[1] + hxhy[1]))
        ring_list.append((vect1[0] + hxhy[0], vect1[1] + hxhy[1]))
        ring_list.append((vect2[0] + hxhy[0], vect2[1] + hxhy[1]))
        ring_list.append((vect3[0] + hxhy[0], vect3[1] + hxhy[1]))
        ring_list.append((vect4[0] + hxhy[0], vect4[1] + hxhy[1]))
        ring_list.append((vect5[0] + hxhy[0], vect5[1] + hxhy[1]))
    return ring_list


def initialize_4_ciliates(brd):
    # Lay 4 ciliates, one in each corner, start with defined colors and center points
    rgb1, rgb2, rgb3, rgb4 = (0, 0, 0), (255, 0, 0), (0, 255, 0), (0, 0, 255)
    dist = 5
    hxhy1_o = (dist, 0)                                       # upper left
    hxhy2_o = (brd.hex_diag - dist, brd.hy_mins[-1 * dist - dist])          # upper right
    hxhy3_o = (dist, brd.hy_maxes[dist + dist])                         # lower left
    hxhy4_o = (brd.hex_diag - dist, 0)                        # lower right
    # Get neighbors of the center points
    neighs1, neighs2, neighs3, neighs4 = (
        Neighbors2Hex(hxhy1_o, brd), Neighbors2Hex(hxhy2_o, brd),
        Neighbors2Hex(hxhy3_o, brd), Neighbors2Hex(hxhy4_o, brd))
    hxhy1 = [neighs1.up_left, hxhy1_o, neighs1.low_right]  # upper left
    hxhy2 = [neighs2.low_left, hxhy2_o, neighs2.up_right]  # upper right
    hxhy3 = [neighs3.low_left, hxhy3_o, neighs3.up_right]  # lower left
    hxhy4 = [neighs4.up_left, hxhy4_o, neighs4.low_right]  # lower right
    return [Ciliate(rgb1, hxhy1, brd), Ciliate(rgb2, hxhy2, brd), Ciliate(rgb3, hxhy3, brd), Ciliate(rgb4, hxhy4, brd)]


def initialize_amoeba(radius, brd):
    # Center of amoeba at center of board
    rgb = (25, 255, 255)
    hxhy_list = [brd.midpoint]
    # use rotation method to make concentric hex rings
    for r in range(1, radius + 1):
        hxhy_list.extend(get_ring(hxhy_list[0], r))
    return Amoeba(rgb, hxhy_list, brd)


def get_image_name(t):
    if 0 <= t <= 9:
        return '00' + str(t)
    elif 10 <= t <= 99:
        return '0' + str(t)
    elif 100 <= t <= 999:
        return str(t)
    else:
        print('Invalid max time step: 0...999 only')
        exit()


def run_simulation(t_max, hex_cnt, width, organisms, img_path):
    # Lay the organisms onto the board and save as first simulation step
    board = Board(hex_cnt, width, img_path + '000', organisms)
    board.save()
    # Separate amoeba and ciliates
    amoeba = organisms.pop()
    ciliates = organisms
    for t in range(1, t_max + 1):
        # Record the time step as the image name to be saved.
        print('Time step:', t)
        img_name = img_path + get_image_name(t)
        # Move the amoeba three times per time step.
        for i in range(3):
            new_hxhy = amoeba.moved_hxhy_list
            amoeba = Amoeba(amoeba.rgb, new_hxhy, board)
            board = Board(hex_cnt, width, img_name, [*ciliates, amoeba])
        # Move the ciliates one time each.
        for i in range(len(ciliates)):
            new_hxhy = ciliates[i].moved_hxhy_list
            ciliates[i] = Ciliate(ciliates[i].rgb, new_hxhy, board)
            board = Board(hex_cnt, width, img_name, [*ciliates, amoeba])
        board.save()
###
def make_video(image_path,fps):
    img_array = []
    for filename in glob.glob(image_path):
        img = cv2.imread(filename)
        height,width,layers = img.shape
        size = (width,height)
        img_array.append(img)
    out = cv2.VideoWritter('final_project.avi'.cv2.VideoWriter_fourcc(*'DIVX'),fps,size)
    for i in range(len(img_array)):
        out.write(img_array[i])
    out.release()

if __name__ == "__main__":
    # Define the board by entering number of hexagons across the diagonal and the pixel width of each hexagon.
    # Knobs: large simulation 120, 36, 10; small simulation 40, 23, 2
    # Looking good with 50, 23, 4 for medium-sized.
    hex_count = 60
    pixel_width_of_hex = 19
    amoeba_radius = 5
    max_time_steps = 250
    image_path = 'D:/SIMULATION PHOTOS/'

    # Initialize and save a blank board to a local folder
    os.mkdir(image_path)
    image_name = image_path + "_Blank Hex Board"
    blank_board = Board(hex_count, pixel_width_of_hex, image_name, organisms=None)
    blank_board.save()

    # Get initial list of organism objects
    collection_of_organisms = [*initialize_4_ciliates(blank_board), initialize_amoeba(amoeba_radius, blank_board)]
    # Run simulation over time steps
    run_simulation(max_time_steps, hex_count, pixel_width_of_hex, collection_of_organisms, image_path)
    fps = 15
    make_video(image_path,fps)

    
    
    # another way to make movies
    # From: https://stackoverflow.com/questions/44947505/how-to-make-a-movie-out-of-images-in-python
    # import os
    # import moviepy.video.io.ImageSequenceClip
    # image_folder='folder_with_images'
    # fps=1
    #
    # image_files = [os.path.join(image_folder,img)
    #                for img in os.listdir(image_folder)
    #                if img.endswith(".png")]
    # clip = moviepy.video.io.ImageSequenceClip.ImageSequenceClip(image_files, fps=fps)
    # clip.write_videofile('my_video.mp4')

    
#     # Use OpenCv to combine the images into a movie
#     image_folder = 'images'
#     video_name = 'video.avi'
#     images = [img for img in os.listdirt(image_folder) if img.endswith(".png")]
#     frame = cv2.imread(os.path.join(image_folder,images[0]))
#     height,width,layers = frame.shape
#     Video = cv2.VideoWriter(video_name,0,1,(width,height))
#     for image in images:
#         video.write(cv2.imread(os.path.join(image_folder,image)))
#     cv2. destroyAllWindows()
#     video.release()
    
    
    # # Delete the image folder once the movie is made and saved elsewhere
    # shutil.rmtree(image_path)
