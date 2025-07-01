from rom import Room, Exit, Coords


def assign_coordinates(rooms):
    # Direction offsets for coordinate changes
    DIRECTION_OFFSETS = {
        "north": (0, 1),
        "east": (1, 0),
        "south": (0, -1),
        "west": (-1, 0),
    }

    coordinates = {}  # Room vnum -> (x, y)
    visited = set()   # Track visited rooms
    occupied = set()  # Track occupied coordinates

    def dfs(room, x, y):
        if room.vnum in visited:
            return
        visited.add(room.vnum)
        coordinates[room.vnum] = (x, y)
        occupied.add((x, y))

        for exit in room.exits:
            neighbor_vnum = exit.to
            if neighbor_vnum not in visited:
                dx, dy = DIRECTION_OFFSETS[exit.direction]
                new_x, new_y = x + dx, y + dy
                while (new_x, new_y) in occupied:  # Adjust to avoid overlap
                    new_x += 1  # Shift to the right if overlap occurs
                dfs(next(r for r in rooms if r.vnum == neighbor_vnum), new_x, new_y)

    # Start with the first room
    if rooms:
        dfs(rooms[0], 0, 0)

    return coordinates


def main():
    rooms = [
        Room(vnum=1000, exits=[Exit(direction="east", to=1001), Exit(direction="south", to=1002)]),
        Room(vnum=1001, exits=[Exit(direction="west", to=1000)]),
        Room(vnum=1002, exits=[Exit(direction="north", to=1000), Exit(direction="east", to=1003)]),
        Room(vnum=1003, exits=[Exit(direction="west", to=1002), Exit(direction="north", to=1004)]),
        Room(vnum=1004, exits=[Exit(direction="south", to=1003)])
    ]

    coordinates = assign_coordinates(rooms)
    for vnum, coord in coordinates.items():
        print(f"Room {vnum} -> {coord}")


if __name__ == "__main__":
    main()