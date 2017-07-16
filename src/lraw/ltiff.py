# -*- coding: utf8 -*-
#
# minimal support to generate TIFF-like file container

import sys, time, struct, types, collections
from array import array

_debug = False


# Tag type enumerate
UINT8  = 1
STRING = 2
UINT16 = 3
UINT32 = 4
RATIONAL = 5
#SINT8  = 6
#SINT16 = 8
SINT32 = 9
SRATIONAL = 10
FLOAT32 = 11
#FLOAT64 = 12



# Minimal useful sub-set from baseline TIFF tag types
TIFF_base_tags = {
    0x00FE : UINT32,    # sub-file type
    0x0100 : UINT32,    # width
    0x0101 : UINT32,    # height
    0x0102 : UINT16,    # bits/sample, can be vector
    0x0103 : UINT16,    # compression (1 - no compression)
    0x0106 : UINT16,    # photometric interpretation
    0x010A : UINT16,    # fill order - N.U.
    0x010D : STRING,    # document name
    0x010E : STRING,    # image name
    0x010F : STRING,    # make
    0x0110 : STRING,    # model
    0x0111 : UINT32,    # strip offset
    0x0112 : UINT16,    # orientation (1 - top,left)
    0x0115 : UINT16,    # samples/pixel i.e. 3 for RGB
    0x0116 : UINT16,    # rows / strip
    0x0117 : UINT32,    # strip byte count
    0x0118 : UINT16,    # min. sample values
    0x0119 : UINT16,    # max. sample values
    0x011A : RATIONAL,  # X resolution
    0x011B : RATIONAL,  # Y resolution
    0x011C : UINT16,    # Planar config., 1 - chunky (like RGB, DNG, 2 - seperate color layers)
    0x011E : RATIONAL,  # X position
    0x011F : RATIONAL,  # Y position
    0x0128 : UINT16,    # resolution unit
    0x0132 : STRING,    # ModifyDate
    0x0142 : UINT16,    # TileWidth
    0x0143 : UINT16,    # TileLength
    0x0144 : UINT32,    # TileOffsets
    0x0145 : UINT32}    # TileByteCounts

EXIM_tags = {
    0x828D : UINT8,     # CFARepeatPatternDim - 2 vector with dimensions of bayer pattern
    0x828E : UINT8,     # CFAPattern2 - the pattern
    0x8298 : STRING,    # Copyright
#    0x882a : UINT16,    # TimeZone
    0x9003 : STRING,    # Time/Date original
    0x9004 : STRING}    # CreateDate


DNG_tags = {
    0xC612 : UINT8,     # 4-vector for revision
    0xC613 : UINT8,     # 4-vector - min. rev. 1.3.0.0 (CFALayout)
    0xC616 : UINT8,     # CFAPlayeColor n-vec
    0xC617 : UINT16,    # CFALayout
    0xC619 : UINT16,    # BlackLevelRepeatDim
    0xC61A : UINT16,    # BlackLevel, could be rational
    0xC61D : UINT16,    # WhiteLevel
    0xC61E : RATIONAL,  # DefaultScale
    0xC61F : UINT32,    # DefaultCropOrigin
    0xC620 : UINT32,    # DefaultCropSize
    0xC621 : SRATIONAL, # ColorMatrix1
    0xC623 : SRATIONAL, # CameraCalibration1
    0xC627 : RATIONAL,  # AnalogBalance
    0xC628 : RATIONAL,  # AsShotNeutral
    0xC62A : SRATIONAL, # BaselineExposure,
    0xC62B : RATIONAL,  # BaselineNoise
    0xC62C : RATIONAL,  # BaselineSharpness
    0xC62E : RATIONAL,  # LinearResponseLimit
    0xC62D : UINT32,    # BayerGreenSplit - arb.
    0xC632 : RATIONAL,  # AntiAliasStrength
    0xC633 : RATIONAL,  # ShadowScale
    0xC65A : UINT16,    # CalibrationIluminant1
    0xC65C : RATIONAL,  # BestQualityScale
    0xC68D : UINT32,    # ActiveArea
    0xC71C : UINT8,     # RawImageDigest
    0xA302 : UINT8}     # CFAPattern - n vector

TIFF_tags = TIFF_base_tags.copy()
TIFF_tags.update(EXIM_tags)
TIFF_tags.update(DNG_tags)



class TiffException(BaseException):

    def __init__(self, txt):
        BaseException.__init__(self, txt)




class IDF_tag(object):

    class emit_desc(object):

        def __init__(self, is_comp, nby, fmt, stride=1):
            self.is_comp = is_comp
            self.nby = nby
            self.fmt = fmt
            self.stride = stride

    emit_desc = { \
        UINT8   : emit_desc(False, 1, '>B'),
        UINT16  : emit_desc(False, 2, '>H'),
        UINT32  : emit_desc(False, 4, '>I'),
        SINT32  : emit_desc(False, 4, '>i'),
        FLOAT32 : emit_desc(False, 4, '>f'),
        STRING  : emit_desc(True, 1, '>B'),
        RATIONAL  : emit_desc(True, 8, '>II', 2),
        SRATIONAL : emit_desc(True, 8, '>ii', 2) }


    def __init__(self, tag, value, tpe=None, cnt=None):

        if tpe is None:
            try:
                tpe = TIFF_tags[tag]
            except KeyError:
                raise TiffException("unknown tag 0x{0:04X}".format(tag))

        # strings special handling, zero padding to DW length
        if isinstance(value, str):
            assert tpe == STRING, "expected string as value"

            # convert to sequence of bytes
            n = len(value)
            value = [ord(c) for c in value]

            cnt = 4*(n/4+1)
            npad = cnt - n
            value = tuple(value + npad*[0])

        desc = IDF_tag.emit_desc[tpe]
        is_seq = isinstance(value, collections.Sequence)
        if cnt is None:
            cnt = len(value) / desc.stride if is_seq else 1

        if not (is_seq or desc.is_comp):
            assert cnt == 1, "expecting single value"
        else:
            n = len(value)
            assert n == cnt*desc.stride, \
                "no. of values in sequence mis-match stride*cnt"
            if is_seq and cnt == 1 and not desc.is_comp:
                value = value[0]

        if _debug:
            print "# init  : tag=0x{0:02X}, type={1}, cnt={2}".format(tag, tpe, cnt)

        # and fill in the blanks
        self.tag = tag
        self.tpe = tpe
        self.cnt = cnt
        self.value = value
        self.txt = None


    def emit_idfe(self, fn):
        tag = self.tag
        tpe = self.tpe
        cnt = self.cnt

        txt = self._pack()

        if _debug:
            print "# emit  : tag=0x{0:02X}, len(buf)={2}".format(tag, cnt, len(txt))

        self.val_ofs = fn.tell() + 8

        if len(txt) > 4:
            # emit value some other place
            self.txt = txt
            buf = struct.pack(">HHII", tag, tpe, cnt, 0xFFFFFFFF)
        else:
            if len(txt) < 4:            # and pad
                txt = txt + (4-len(txt))*chr(0)
            buf = struct.pack(">HHI", tag, tpe, cnt) + txt
        fn.write(buf)


    def emit_value(self, fn):
        "output packed value, if needed i.e. not output in IDF"

        if self.txt is None:
            return

        # back-patch tag value to point here
        ofs = fn.tell()
        fn.seek(self.val_ofs)
        fn.write(struct.pack(">I", ofs))
        fn.seek(ofs)

        if _debug:
            print "# emit-v: tag=0x{0:02X} @ 0x{1:08X}".format(self.tag, ofs)
        fn.write(self.txt)



    def _pack(self):
        cnt = self.cnt
        val = self.value

        desc = IDF_tag.emit_desc[self.tpe]
        stride = desc.stride
        fmt = desc.fmt
        if cnt == 1:
            if stride == 1:
                txt = struct.pack(fmt, val)
            else:
                txt = struct.pack(fmt, *val)
        else:
            txt = ''
            for jj in range(cnt):
                if stride == 1:
                    txt = txt + struct.pack(fmt, val[jj])
                else:
                    l = jj*stride
                    h = l + stride
                    txt = txt + struct.pack(fmt, *val[l:h])

        return txt


# ---------------------------------------------------------------------
class Image(object):
    """base class for all flavours of images
    """

    def __init__(self):
        self.IDF = {}
        self.data = None
        self._init_links()
        self.add_tag(0x0FE, 0, tpe=UINT32)         # new subfile

    # -----------------------------------------------------------------
    # methods to populate the meta-data, but the set_data methods must
    # be implemented in the actual image class since knows how the
    # image is organised


    def set_model(self, model, make):
        self.add_tag(0x10F, str(model))
        self.add_tag(0x110, str(make))


    def set_image_desc(self, txt):
        self.add_tag(0x10e, str(txt))

    def set_copyright(self, txt):
        self.add_tag(0x10e, str(txt))

    def set_data(self, width, height, ns_px, nbps, mn, mx, data):
        """initialize data and minimal description

        usage: set_data(w, h, ns_px, nbps, mn, mx, data):
          w     - no. of pixels in X dimension
          h     - no. of pixels in Y dimension
          ns_px - no. of samples/pixel
          nbps  - no. of bits/sample
          mn    - min sample value
          mx    - max sample value
          data  - opaque string/bytearray, output as is
        """

        assert width > 0, "width must be > 0"
        assert height > 0, "height must be > 0"

        n = len(data)
        self.data = data
        self.width = width
        self.height = height
        self.ns_px = ns_px
        self.nbps = nbps
        self.sampl_min = mn
        self.sampl_max = mx

        self.add_tag(0x0100, width)
        self.add_tag(0x0101, height)

        # do we really need this?
        #self.add_tag(0x0118, mn)
        #self.add_tag(0x0119, mx)

        self.add_tag(0x0115, ns_px)             # samples/pixel
        self.add_tag(0x0102, ns_px*[nbps])      # bits/sample

        self.add_tag(0x116, self.height)        # rows/strip

        n = len(data)
        self.add_tag(0x0117, n)                 # bytes/strip

        self.add_tag(0x111, 0)      # strip offset - backpatched

        # resolution : 150 ppi (arb)
        self.add_tag(0x11a, [450, 3])           # Xres: arb. 150p
        self.add_tag(0x11b, [450, 3])
        self.add_tag(0x128, 2)                  # units: inch

        # fillorder
        tm = time.localtime()
        txt = time.strftime("%Y:%m:d %H:%M:S", tm)
        self.add_tag(0x0132, txt)


    # ---------------------------------------------------------
    # output
    def write_IDF(self, fn):
        "write IDF and value block"

        keyl = self.IDF.keys()
        keyl.sort()

        #  actual IDF, starting with no. of entries
        self.IDF_ofs = fn.tell()
        print "IDF @ 0x{0:08X}".format(self.IDF_ofs)

        # no. of entries in IDF
        txt = struct.pack(">H", len(keyl))
        fn.write(txt)

        for k in keyl:
            entry = self.IDF[k]
            entry.emit_idfe(fn)

        # and record where ptr to next IDF is written
        self.next_link_ofs = fn.tell()
        txt = struct.pack(">I", 0)
        fn.write(txt)

        # for composites, emit values
        for k in keyl:
            entry = self.IDF[k]
            entry.emit_value(fn)


    def write_data(self, fn):
        """write the image data using the supplied struct.pack format
        """

        ofs = fn.tell()
        if (ofs % 4) != 0:
            txt = (ofs % 4) * chr(0)
            fn.write(txt)

        self.img_ofs = fn.tell()
        print "data @ 0x{0:08X}".format(self.img_ofs)

        fn.write(self.data)

        n = len(self.data)
        if (n % 4) != 0:
            txt = (n % 4) * chr(0)
            fn.write(txt)

        # back-patch strip offset
        ofs = fn.tell()
        entry = self.IDF[0x111]
        fn.seek(entry.val_ofs)
        fn.write(struct.pack(">I", self.img_ofs))
        fn.seek(ofs)

    # -----------------------------------------------------------------
    def add_tag(self, tag, value, tpe=None, cnt=None):
        """construct IDF entry and add to IDF
        """
        e = IDF_tag(tag, value, tpe=tpe, cnt=cnt)
        self.IDF[tag] = e

    def add_rat_tag(self, tag, a, b, tpe=None, cnt=None):
        """build value for RATIONAL and SRATIONAL type from a and b
        """

        assert len(a) == len(b), "a and b length mis-match"

        n = len(a)
        val = []
        for jj in range(n):
            val.append(a[jj])
            val.append(b[jj])

        e = IDF_tag(tag, val, tpe=tpe, cnt=cnt)
        self.IDF[tag] = e


    # -----------------------------------------------------------------
    def _init_links(self):
        "required file-offsets needed to complete TIFF"
        self.img_ofs = None
        self.IDF_ofs = None
        self.next_link_ofs = None


class RGB_Image(Image):
    """TIFF image container, mostly to allow test images
    """

    def __init__(self):
        Image.__init__(self)


    def set_data(self, w, h, data):
        """initialize data from sequence of RGB data

        usage: set_data(w, h, data)
        """

        super(RGB_Image, self)

        ns_px = 3          # samples/pixel i.e. R,G,B
        mn, mx = min(data), max(data)
        nbyps = 2 if mx >= 256 else 1

        txt = self.convert_data(w, h, nbyps, data)
        super(RGB_Image, self).set_data(w, h, ns_px, 8*nbyps, mn, mx, txt)

        self.add_tag(0x0103, 1)    # uncompressed
        self.add_tag(0x0106, 2)    # photometric: RGB
        self.add_tag(0x0112, 1)    # orient: top, left
        self.add_tag(0x011C, 1)    # Planar config: chunky


    @staticmethod
    def convert_data(w, h, nbps, data):
        if nbps == 1:
            a = array('B', data)
        else:
            # i.e. 16-bit
            a = array('H', data)
            if sys.byteorder == 'little':
                a.byteswap()
        return a.tostring()



class TIFF(object):
    """container object for all the images in a tiff file
    """

    def __init__(self):
        self.images = []

    def add_image(self, img):
        self.images.append(img)

    def write(self, fname):
        print ".. write tiff file: {0}".format(fname)

        with open(fname, 'wb') as fn:
            self._wr_hdr(fn)

            for img in self.images:
                img.write_IDF(fn)

            # write all the image's data
            for img in self.images:
                img.write_data(fn)

            # and back-patch IDF links
            lnk_ofs = 4
            for img in self.images:
                fn.seek(lnk_ofs)
                txt = struct.pack(">I", img.IDF_ofs)
                fn.write(txt)
                lnk_ofs = img.next_link_ofs


    # ---------------------------------------------------------
    def _wr_hdr(self, fn):
        ofs = 0           # place holder
        txt = struct.pack(">HHI", 0x4D4D, 0x02A, ofs)
        fn.write(txt)

