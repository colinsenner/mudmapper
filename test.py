from rom import Room, Exit, Coords

def mul(t: tuple, scalar: int):
    return tuple(x * scalar for x in t)

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
                scalar = 1024
                direction = DIRECTION_OFFSETS[exit.direction]
                dx, dy, dz = mul(direction, scalar) 
                
                new_x, new_y, new_z = x + dx, y + dy, z + dz

                while (new_x, new_y, new_z) in occupied:  # Adjust to avoid overlap
                    scalar /= 2

                    if scalar < 1:
                        print(f"Error, can't subdivide the distance any more.")
                        exit(1)

                    new_x, new_y, new_z = (new_x + direction[0] * scalar, new_y + direction[1] * scalar, new_z + direction[2] * scalar)

                tmp = list(r for r in rooms if r.vnum == neighbor_vnum) 
                if len(tmp) > 0:
                    dfs(next(r for r in rooms if r.vnum == neighbor_vnum), new_x, new_y, new_z)

    # Start with the first room
    if rooms:
        dfs(rooms[0], 0, 0, 0)

    return normalize(coordinates)


def normalize(coordinates: dict):
    # Normalize the room positions to be within more normal values
    smallest_coord = max([abs(min(coord)) for coord in coordinates.values()])
    return {vnum:(int(coord[0] / smallest_coord), int(coord[1] / smallest_coord), int(coord[2] / smallest_coord)) for vnum, coord in coordinates.items()}


def main():
    rooms = [
        Room(vnum=1000, exits=[Exit(direction="DIR_EAST", to=1003), Exit(direction="DIR_SOUTH", to=1002)]),
        Room(vnum=1001, exits=[Exit(direction="DIR_WEST", to=1000)]),
        Room(vnum=1002, exits=[Exit(direction="DIR_NORTH", to=1000), Exit(direction="DIR_EAST", to=1003)]),
        Room(vnum=1003, exits=[Exit(direction="DIR_WEST", to=1002), Exit(direction="DIR_NORTH", to=1004)]),
        Room(vnum=1004, exits=[Exit(direction="DIR_SOUTH", to=1003)])
    ]

    coordinates = assign_coordinates(rooms)
    for vnum, coord in coordinates.items():
        print(f"Room {vnum} -> {coord}")


if __name__ == "__main__":
    main()