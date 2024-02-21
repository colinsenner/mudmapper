"""
Defines from merc.h
"""


def dir_to_direction(dir):
    return dir.replace("DIR_", "").lower()


room_flags = {
    'A': 'ROOM_DARK',
    'C': 'ROOM_NO_MOB',
    'D': 'ROOM_INDOORS',
    'J': 'ROOM_PRIVATE',
    'K': 'ROOM_SAFE',
    'L': 'ROOM_SOLITARY',
    'M': 'ROOM_PET_SHOP',
    'N': 'ROOM_NO_RECALL',
    'O': 'ROOM_IMP_ONLY',
    'P': 'ROOM_GODS_ONLY',
    'Q': 'ROOM_HEROES_ONLY',
    'R': 'ROOM_NEWBIES_ONLY',
    'S': 'ROOM_LAW',
    'T': 'ROOM_NOWHERE'
}

room_directions = {
    0: 'DIR_NORTH',
    1: 'DIR_EAST',
    2: 'DIR_SOUTH',
    3: 'DIR_WEST',
    4: 'DIR_UP',
    5: 'DIR_DOWN',
}

sector_types = {
    -1: 'SECT_UNKNOWN',     # The immort.are has a room tagged -1
    0: 'SECT_INSIDE',
    1: 'SECT_CITY',
    2: 'SECT_FIELD',
    3: 'SECT_FOREST',
    4: 'SECT_HILLS',
    5: 'SECT_MOUNTAIN',
    6: 'SECT_WATER_SWIM',
    7: 'SECT_WATER_NOSWIM',
    8: 'SECT_UNUSED',
    9: 'SECT_AIR',
    10: 'SECT_DESERT',
    11: 'SECT_MAX',
}


def get_flag_names(flags):
    names = []
    for flag in list(flags):
        if flag in room_flags:
            names.append(room_flags[flag])

    return names


def get_direction_name(dir):
    assert dir in room_directions, "Not a valid direction"
    return room_directions[dir]


def get_sector_type(type):
    return sector_types[type]