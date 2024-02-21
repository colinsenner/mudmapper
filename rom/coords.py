import copy


class Coords:
    '''Coordinates x,y,z to map rooms'''
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

    @staticmethod
    def from_direction(coords, direction):
        coords = copy.copy(coords)

        assert direction in ['north', 'south', 'east', 'west', 'up', 'down'], f"Invalid exit direction {direction}"

        if direction == 'north':
            coords.y += 1
        elif direction == "east":
            coords.x += 1
        elif direction == "south":
            coords.y -= 1
        elif direction == "west":
            coords.x -= 1
        elif direction == "up":
            coords.z += 1
        elif direction == "down":
            coords.z -= 1

        return coords

    def __str__(self):
        return f"Coords(x={self.x}, y={self.y}, z={self.z})"
