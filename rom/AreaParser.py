import collections
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


# Used for BFS (kept for backwards compatibility; no longer required by the
# updated bfs implementation below).
visited = []
queue = []


# (dx, dy, dz) deltas for each cardinal direction.
_DIR_DELTAS = {
    'north': ( 0,  1,  0),
    'south': ( 0, -1,  0),
    'east':  ( 1,  0,  0),
    'west':  (-1,  0,  0),
    'up':    ( 0,  0,  1),
    'down':  ( 0,  0, -1),
}

# Maximum number of steps to walk along a direction before giving up and
# falling back to the naive position. Areas in the wild can be large but are
# rarely deeper than this along a single axis.
_MAX_PLACEMENT_STEPS = 500


def _cells_between(a, b):
    '''Cells strictly between two coords on the same axis (exclusive of endpoints).'''
    ax, ay, az = a
    bx, by, bz = b
    cells = []
    if ax == bx and ay == by and az != bz:
        step = 1 if bz > az else -1
        for z in range(az + step, bz, step):
            cells.append((ax, ay, z))
    elif ax == bx and az == bz and ay != by:
        step = 1 if by > ay else -1
        for y in range(ay + step, by, step):
            cells.append((ax, y, az))
    elif ay == by and az == bz and ax != bx:
        step = 1 if bx > ax else -1
        for x in range(ax + step, bx, step):
            cells.append((x, ay, az))
    return cells


def _direction_from(a, b):
    '''Cardinal direction from a to b if they share two axes, otherwise None.'''
    ax, ay, az = a
    bx, by, bz = b
    if ax == bx and ay == by and az != bz:
        return 'up' if bz > az else 'down'
    if ax == bx and az == bz and ay != by:
        return 'north' if by > ay else 'south'
    if ay == by and az == bz and ax != bx:
        return 'east' if bx > ax else 'west'
    return None


def _find_placement(current, direction, occupied, line_cells, graph,
                    nb_vnum, map_coords):
    '''
    Find a position for nb_vnum being placed *direction* from *current*.

    Walks step-by-step in *direction* until it finds a candidate that:
      1. Is unoccupied and not on an existing connection line.
      2. Has a clear path (no rooms) from *current* to the candidate.
      3. Doesn't break already-placed neighbours of nb_vnum: each placed
         neighbour must lie in the correct cardinal direction from the
         candidate, with a clear path.
      4. Doesn't trap unplaced neighbours of nb_vnum: the immediate cell in
         each of nb_vnum's other exit directions must not already be
         occupied or on a connection line.
    '''
    dx, dy, dz = _DIR_DELTAS[direction]
    cx, cy, cz = current
    nb_exits = graph.get(nb_vnum, {})

    for step in range(1, _MAX_PLACEMENT_STEPS + 1):
        candidate = (cx + dx * step, cy + dy * step, cz + dz * step)

        if candidate in occupied:
            continue
        if candidate in line_cells:
            continue

        path = _cells_between(current, candidate)
        if any(c in occupied for c in path):
            continue

        ok = True
        for other_vnum, other_dir_raw in nb_exits.items():
            other_dir = dir_to_direction(other_dir_raw)
            if other_vnum in map_coords:
                other_pos = map_coords[other_vnum]
                if _direction_from(candidate, other_pos) != other_dir:
                    ok = False
                    break
                if any(c in occupied for c in _cells_between(candidate, other_pos)):
                    ok = False
                    break
            else:
                odx, ody, odz = _DIR_DELTAS[other_dir]
                immediate = (candidate[0] + odx, candidate[1] + ody, candidate[2] + odz)
                if immediate in occupied or immediate in line_cells:
                    ok = False
                    break

        if ok:
            return candidate

    # Fallback — walk along the direction until we find any unoccupied cell.
    # This guarantees no overlap, at the cost of relaxing path/lookahead checks.
    step = 1
    while True:
        candidate = (cx + dx * step, cy + dy * step, cz + dz * step)
        if candidate not in occupied:
            return candidate
        step += 1


def bfs(visited, graph, map_coords, node):
    '''
    Coordinate-assigning BFS that avoids two failure modes:
      1. Rooms overlapping at the same cell (ISSUE-1).
      2. Connection lines passing through other rooms (ISSUE-2).

    The *visited* and *map_coords* arguments are mutated in place for
    backwards compatibility with the original signature. Internally the
    function tracks its own visited set so successive calls with a stale
    module-level list don't poison the search.
    '''
    seen = {node}
    visited.append(node)
    bfs_queue = collections.deque([node])

    start = (0, 0, 0)
    coord_map = {node: start}        # vnum -> (x, y, z)
    occupied = {start: node}         # (x, y, z) -> vnum
    line_cells = set()               # cells covered by connection segments

    while bfs_queue:
        vnum = bfs_queue.popleft()

        if vnum not in graph:
            print(f"[WARNING] Found vnum {vnum} which isn't in our graph, it's probably a connecting door to another area.")
            continue

        current = coord_map[vnum]

        for neighbour, direction_raw in graph[vnum].items():
            if neighbour in seen:
                continue

            direction = dir_to_direction(direction_raw)
            seen.add(neighbour)
            visited.append(neighbour)
            bfs_queue.append(neighbour)

            pos = _find_placement(current, direction, occupied, line_cells,
                                  graph, neighbour, coord_map)

            coord_map[neighbour] = pos
            occupied[pos] = neighbour

            # Record line cells for the new connection (parent <-> neighbour)
            # and for any back-edges to already-placed rooms.
            for cell in _cells_between(current, pos):
                line_cells.add(cell)
            for other_vnum, other_dir_raw in graph.get(neighbour, {}).items():
                if other_vnum == vnum or other_vnum not in coord_map:
                    continue
                other_pos = coord_map[other_vnum]
                if _direction_from(pos, other_pos) == dir_to_direction(other_dir_raw):
                    for cell in _cells_between(pos, other_pos):
                        line_cells.add(cell)

    for vnum, (x, y, z) in coord_map.items():
        map_coords[vnum] = Coords(x, y, z)

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
