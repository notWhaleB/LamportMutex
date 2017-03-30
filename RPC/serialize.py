DELIM = "\t"
END = "\n"

def serialize(cmd, *args):
    return DELIM.join(map(str, [cmd] + list(args))) + END


def unserialize(data):
    components = data.split(DELIM)
    cmd = components[0]
    args = components[1:]

    return cmd, args