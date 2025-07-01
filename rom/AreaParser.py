import json
from dataclasses import dataclass, field
from typing import List, Optional

from rom.coords import Coords

from .FileIO import (fread_letter, fread_number, fread_string, fread_until,
                     fread_word)
from .merc import get_direction_name, get_flag_names, get_sector_type, dir_to_direction


@dataclass
class Exit():
    direction: str = None
    to: int = None
    keyword: Optional[str ] = None
    description: Optional[str] = None
    locks: Optional[str] = None
    key: Optional[str] = None
    exit_info: Optional[str] = None


@dataclass
class Room():
    vnum: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    flags: Optional[List[str]] = field(default_factory=list)
    sector_type: Optional[str] = None
    extra_descr_data: Optional[dict] = field(default_factory=dict)
    exits: Optional[List[Exit]] = field(default_factory=list)
    coords: Optional[Coords] = None


def assign_coordinates(rooms):
    # Direction offsets for coordinate changes, including Z-axis
    DIRECTION_OFFSETS = {
        "DIR_NORTH": (0, 1, 0),
        "DIR_EAST": (1, 0, 0),
        "DIR_SOUTH": (0, -1, 0),
        "DIR_WEST": (-1, 0, 0),
        "DIR_UP": (0, 0, 1),
        "DIR_DOWN": (0, 0, -1),
    }

    coordinates = {}  # Room vnum -> (x, y, z)
    visited = set()   # Track visited rooms
    occupied = set()  # Track occupied coordinates

    def dfs(room, x, y, z):
        if room.vnum in visited:
            return
        visited.add(room.vnum)
        coordinates[room.vnum] = (x, y, z)
        occupied.add((x, y, z))

        for exit in room.exits:
            neighbor_vnum = exit.to
            if neighbor_vnum not in visited:
                dx, dy, dz = DIRECTION_OFFSETS[exit.direction]
                new_x, new_y, new_z = x + dx, y + dy, z + dz
                while (new_x, new_y, new_z) in occupied:  # Adjust to avoid overlap
                    new_x += 1  # Shift to the right if overlap occurs

                tmp = list(r for r in rooms if r.vnum == neighbor_vnum) 
                if len(tmp) > 0:
                    dfs(next(r for r in rooms if r.vnum == neighbor_vnum), new_x, new_y, new_z)

    # Start with the first room
    if rooms:
        dfs(rooms[0], 0, 0, 0)

    return coordinates


class Area():
    def __init__(self):
        self.filename = None
        self.name = None
        self.credits = None
        self.min_vnum = None
        self.max_vnum = None
        self.rooms = []

    def __str__(self):
        printable = f"Area(name='{self.name}', filename='{self.filename}', file='{self.file}'))"
        return printable

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=2)

    @staticmethod
    def load(file):
        area = Area()
        area.file = file

        with open(file, "rt") as fs:
            while True:
                letter = fread_letter(fs)
                assert letter == "#", "# not found"

                word = fread_word(fs)

                if word == "AREA":
                    print("Parsing #AREA...")
                    # Load area
                    area.filename = fread_string(fs)
                    area.name = fread_string(fs)
                    area.credits = fread_string(fs)
                    area.min_vnum = fread_number(fs)
                    area.max_vnum = fread_number(fs)
                    print("Parsed #AREA")
                elif word == "ROOMS":
                    # Load rooms
                    print("Parsing #ROOMS...")
                    area.rooms = Area.load_rooms(fs)

                    # After we load rooms, we're done!
                    print("Parsed #ROOMS")

                    # Give rooms coordinates
                    Area.assign_room_coords(area)

                    break
                else:
                    # We don't have an entry for things like #MOBILES #OBJECTS
                    fread_until(fs, "#0")
                    print(f"Skipping section {word}...")

        return area

    @staticmethod
    def assign_room_coords(area):
        '''Assigns each room a coord x,y,z'''
        print("Assigning rooms coordinates...")

        # Breadth-first search through the map to visit all rooms and return their coordinates
        map_coords = assign_coordinates(area.rooms)

        for room in area.rooms:
            # Assign each room its coordinates

            # Some rooms, like pet store shops have no exits and must follow the pet store room
            if room.vnum not in map_coords:
                print(f"[WARNING] Room {room.vnum} was not found in our search, it may be a pet store with no exits.  Room name: '{room.name}'.")
                continue

            coords = map_coords[room.vnum]
            room.coords = Coords(*coords)  # Assign x, y, z as Coords object

        print("Coordinates assigned")


    @staticmethod
    def load_rooms(fs):
        rooms = []

        while True:
            # Line 1123 db.c
            room = Room()

            letter = fread_letter(fs)
            assert letter == "#", "# not found"

            vnum = fread_number(fs)

            # #0 done
            if vnum == 0:
                break

            room.vnum = vnum

            room.name = fread_string(fs)
            room.description = fread_string(fs)
            _ = fread_number(fs)
            room.flags = get_flag_names(fread_word(fs))
            room.sector_type = get_sector_type(fread_number(fs))

            while True:
                letter = fread_letter(fs)

                assert letter == 'S' or letter == 'H' or letter == 'M' or letter == 'C' or letter == 'D' or letter == 'E' or letter == 'O', f"Letter '{letter}' unrecognized!"

                if letter == 'S':
                    # End of this room
                    break

                if letter == 'H':
                    # Health regen room
                    room.heal_rate = fread_number(fs)
                elif letter == 'M':
                    # Mana regen room
                    room.mana_rate = fread_number(fs)
                elif letter == 'C':
                    # Clan
                    room.clan = fread_string(fs)
                elif letter == 'D':
                    # Exits
                    exit = Exit()

                    door = fread_number(fs)
                    assert door >= 0 and door <= 5, f"vnum {vnum} has bad door number."
                    exit.direction = get_direction_name(door)

                    exit.description = fread_string(fs)
                    exit.keyword = fread_string(fs)
                    locks = fread_number(fs)
                    exit.key = fread_number(fs)
                    exit.to = fread_number(fs)

                    if locks == 1:
                        exit.exit_info = ['EX_ISDOOR']
                    elif locks == 2:
                        exit.exit_info = ['EX_ISDOOR', 'EX_PICKPROOF']
                    elif locks == 3:
                        exit.exit_info = ['EX_ISDOOR', 'EX_NOPASS']
                    elif locks == 4:
                        exit.exit_info = ['EX_ISDOOR', 'EX_NOPASS', 'EX_PICKPROOF']

                    # Add exits to rooms
                    room.exits.append(exit)

                elif letter == 'E':
                    # Exit extra description information
                    room.extra_descr_data['keyword'] = fread_string(fs)
                    room.extra_descr_data['description'] = fread_string(fs)
                elif letter == 'O':
                    # Owner
                    room.owner = fread_string(fs)

            rooms.append(room)

        return rooms
