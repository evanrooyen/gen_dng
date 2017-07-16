
class IDF_int_tag(object):
    """container for image integer meta-data ie. unsigned 8/16/32
    and signed int32
    """

    pack_fmt = {UINT8 : '>B', UINT16 : '>H', UINT32 : '>I',
                SINT32 : '>i' }

    def __init__(self, tag, cnt, val):
        try:
            tpe = TIFF_tags[tag]
        except KeyError:
            raise Error("unknown tag=0x{0:3X}, value={1}".format(tag, value))

        self.tag = tag
        self.tpe = tpe
        self.count = cnt
        self.value = val

        if _debug:
            print "# int_tag 0x{0:04X}, cnt={1}, value={2}".format(tag, cnt, val)


    def emit_idfe(self, fn):
        n = self.count
        tpe = self.tpe
        if n > 1:
            self.val_ofs = fn.tell() + 8
            buf = struct.pack(">HHII", self.tag, tpe, n, 0xFFFFFFFF)
        else:
            self.val_ofs = fn.tell() + 8

            # pack value into offset field
            if tpe == UINT8:
                buf = struct.pack(">HHIBBBB", self.tag, tpe, 1, self.value, 0, 0, 0)
            if tpe == UINT16:
                buf = struct.pack(">HHIHH", self.tag, tpe, 1, self.value, 0)
            if tpe == UINT32:
                buf = struct.pack(">HHII", self.tag, tpe, 1, self.value)
            if tpe == SINT32:
                buf = struct.pack(">HHII", self.tag, tpe, 1, self.value)

        fn.write(buf)

    def emit_value(self, fn):
        if self.count == 1:
            return
        ofs = fn.tell()
        print "int_tag value @ 0x{0:08X}".format(ofs)

        fn.seek(self.val_ofs)
        fn.write(struct.pack(">I", ofs))

        fn.seek(ofs)
        fmt = IDF_int_tag.pack_fmt[self.tpe]
        for x in self.value:
            fn.write(struct.pack(fmt, x))
        if self.tpe == UINT8 and (self.count % 2) == 1:
            fn.write(chr(0))



class IDF_str_tag(object):

    def __init__(self, tag, value):
        try:
            tpe = TIFF_tags[tag]
        except KeyError:
            raise Error("unknown tag=0x{0:3X}, value={1}".format(tag, value))
        if tpe != STRING:
            raise Error("tag=0x{3X}, must be string, value={1}".format(tag, value))

        self.tag = tag
        self.tpe = STRING
        n = len(value)
        self.count = 4*(n/4 + 1)
        self.value = value

        if _debug:
            print "# str_tag 0x{0:04X}, cnt={1}, value={2}".format(tag, self.count, value)


    def emit_idfe(self, fn):
        self.val_ofs = fn.tell() + 8
        buf = struct.pack(">HHII", self.tag, self.tpe, self.count, 0xFFFFFFFF)
        fn.write(buf)

    def emit_value(self, fn):
        ofs = fn.tell()
        print "str_tag value @ 0x{0:08X}".format(ofs)
        fn.seek(self.val_ofs)
        fn.write(struct.pack(">I", ofs))

        fn.seek(ofs)
        npad = self.count - len(self.value)
        txt = self.value + npad*chr(0)
        fn.write(txt)


class IDF_rational_tag(object):

    def __init__(self, tag, value):
        try:
            tpe = TIFF_tags[tag]
        except KeyError:
            raise Error("unknown tag=0x{0:3X}, value={1}".format(tag, value))

        if tpe != RATIONAL:
            raise Error("tag=0x{3X}, must be string, value={1}".format(tag, value))

        self.tag = tag
        self.tpe = RATIONAL

        n = len(value)
        assert (n % 2) == 0, "no. of values must be even"
        self.count = n/2
        self.value = value

        if _debug:
            print "# rat_tag 0x{0:04X}, cnt={1}, value={2}".format(tag, n/2, value)


    def emit_idfe(self, fn):
        self.val_ofs = fn.tell() + 8
        buf = struct.pack(">HHII", self.tag, self.tpe, self.count, 0xFFFFFFFF)
        fn.write(buf)

    def emit_value(self, fn):
        ofs = fn.tell()
        print "rat_tag value @ 0x{0:08X}".format(ofs)
        fn.seek(self.val_ofs)
        fn.write(struct.pack(">I", ofs))

        fn.seek(ofs)
        val = self.value
        for jj in range(self.count):
            buf = struct.pack(">II", val[2*jj], val[2*jj+1])
            fn.write(buf)


class IDF_srational_tag(object):

    def __init__(self, tag, value):
        try:
            tpe = TIFF_tags[tag]
        except KeyError:
            raise Error("unknown tag=0x{0:3X}, value={1}".format(tag, value))

        if tpe != SRATIONAL:
            raise Error("tag=0x{3X}, must be string, value={1}".format(tag, value))

        self.tag = tag
        self.tpe = RATIONAL

        n = len(value)
        assert (n % 2) == 0, "no. of values must be even"
        self.count = n/2
        self.value = value

        if _debug:
            print "# rat_tag 0x{0:04X}, cnt={1}, value={2}".format(tag, n/2, value)


