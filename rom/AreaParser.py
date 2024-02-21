import json

from rom.coords import Coords

from .FileIO import (fread_letter, fread_number, fread_string, fread_until,
                     fread_word)
from .merc import get_direction_name, get_flag_names, get_sector_type, dir_to_direction


class Exit():
    def __init__(self):
        self.direction = None
        self.to = None
        self.keyword = None
        self.description = None
        self.locks = None
        self.key = None
        self.exit_info = None

    def __str__(self):
        return f"Exit(direction={self.direction}, to={self.to}, keyword='{self.keyword}', locks={self.locks}, key={self.key}, exit_info={self.exit_info})"


class Room():
    def __init__(self):
        self.vnum = None
        self.name = None
        self.description = None
        self.flags = []
        self.sector_type = None
        self.extra_descr_data = {}
        self.exits = []
        self.coords = None

    def __repr__(self):
        return self.__dict__

    def __str__(self):
        printable = f"Room(vnum={self.vnum}, name='{self.name}', flags={self.flags}, sector_type='{self.sector_type}')\n"

        for exit in self.exits:
            printable += "  " + str(exit) + '\n'

        return printable


# Used for BFS
visited = []
queue = []


def bfs(visited, graph, map_coords, node):
    '''Literally haven't ever had to use this skill unless it was a technical interview...'''
    visited.append(node)
    queue.append(node)

    map_coords[node] = Coords(0, 0, 0)

    while queue:
        vnum = queue.pop(0)

        if vnum not in graph:
            print(f"[WARNING] Found vnum {vnum} which isn't in our graph, it's probably a connecting door to another area.")
            continue

        current_room_location = map_coords[vnum]

        for k, v in graph[vnum].items():
            neighbour = k
            direction = dir_to_direction(v)

            if neighbour not in visited:
                visited.append(neighbour)
                queue.append(neighbour)

                position = Coords.from_direction(current_room_location, direction)
                # print(f"{neighbour:>7} is {direction:>8} from {vnum:>7} at {position}")
                map_coords[neighbour] = position

    return map_coords


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

        # gridmap = GridMap()

        # Create a graph structure
        graph = {room.vnum: {e.to: e.direction for e in room.exits} for room in area.rooms}

        # Breadth-first search through the map to visit all rooms and return their coordinates
        map_coords = bfs(visited, graph, {}, area.rooms[0].vnum)

        # Mapping of the coordinates to the rooms which are at them
        coords_to_rooms = {}

        for room in area.rooms:
            # Assign each room its coordinates

            # Some rooms, like pet store shops have no exits and must follow the pet store room
            if room.vnum not in map_coords:
                print(f"[WARNING] Room {room.vnum} was not found in our search, it may be a pet store with no exits.  Room name: '{room.name}'.")
                continue

            coords = map_coords[room.vnum]
            room.coords = coords

            # Check for stacked rooms
            if str(coords) not in coords_to_rooms:
                coords_to_rooms[str(coords)] = []
            coords_to_rooms[str(coords)].append(room.vnum)

        for coords, rooms in coords_to_rooms.items():
            if len(rooms) > 1:
                print(f"[WARNING] Rooms {rooms} are stacked on each other.")

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
