import copy
from dataclasses import dataclass


@dataclass
class Coords:
    x: int
    y: int
    z: int

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
