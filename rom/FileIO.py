'''C-like parsing for the .are files'''


def fread_letter(fs):
    '''Read a single letter from the filestream, ignore whitespaces'''
    while True:
        c = fs.read(1)

        if not c.isspace():
            break
    return c


def fread_word(fs):
    word = ""

    while True:
        c = fs.read(1)

        if not c.isspace():
            break

    while not c.isspace():
        word += c
        c = fs.read(1)

    return word


def fread_number(fs):
    '''Read number from the filestream, ignore whitespaces'''
    negative = False

    while True:
        c = fs.read(1)

        if not c.isspace():
            break

    number = 0

    if c == '+':
        c = fs.read(1)
    elif c == '-':
        negative = True
        c = fs.read(1)

    if not c.isdigit():
        raise "fread_number: bad format."

    while c.isdigit():
        number = number * 10 + int(c)
        c = fs.read(1)

    if negative:
        number = 0 - number

    # Unsupported | operators
    if c == '|':
        raise "Unsupported | operators "

    return number


def fread_until(fs, match):
    '''Used to skip sections we don't have parsing info for #MOBILES #OBJECTS etc'''
    while True:
        line = fs.readline()

        # the actual line will be '#0\n', ignore the whitespace
        if line.rstrip() == match:
            break


def fread_string(fs):
    '''A string is read until '~' is reached'''
    result = ""

    while True:
        c = fs.read(1)

        if not c.isspace():
            break

    if c == '~':
        return ""

    result += c

    while True:
        c = fs.read(1)

        if c == '\n':
            result += c
            result += '\r'
            continue
        elif c == '\r':
            continue
        elif c == '~':
            return result
        else:
            result += c
