# -*- coding: utf8 -*-
#
# Use 'big-endian' convention

import sys, struct, time, hashlib, math
from array import array
from lraw import ltiff


class DNG_Image(ltiff.Image):

    def __init__(self):
        ltiff.Image.__init__(self)

        # DNG versions
        self.add_tag(0xC612, (1,3,0,0))     # DNG version
        self.add_tag(0xC613, (1,1,0,0))     #


    def set_data(self, w, h, data):
        """set image size and data, and some sub-set of tags

        usage: set_data(self, w, h, data)
        w - image width
        h - image height
        data - array with RGB numbers, std. Bayer filter will be applied
        """
        ns_px = 1
        nbps = 16

        assert (w % 2) == 0 and (h % 2) == 0, \
            "expect even image size"

        # apply color filter to RGB image and pack into byte array
        txt, mn, mx = self.convert_data(w, h, data)
        super(DNG_Image, self).set_data(w, h, ns_px, nbps, mn, mx, txt)

        # populate TIFF fields
        self.add_tag(0x0103, 1)         # uncompressed
        self.add_tag(0x0106, 0x8023)    # photometric: CFA
        self.add_tag(0x0112, 1)         # orient: top, left
        self.add_tag(0x011C, 1)         # Planar config: chunky

        self.add_tag(0x828d, [2,2])         # CFA repeat dim
        self.add_tag(0x828e, [1, 0, 2, 1])  # CFA Pattern  - Bayer
        self.add_tag(0xc617, 1)             # Layout - rectangleg

        a, b = [1,1], [1,1]
        self.add_rat_tag(0xc61e, a, b)      # default scale

        self.add_tag(0xc619, [1,1])     # black rep.
        self.add_tag(0xc61a, mn)        # black level

        nbi = math.ceil(math.log(mx)/math.log(2))
        self.add_tag(0xc61d, 2**nbi-1)  # white level

        self.add_tag(0xc68d, [0,0, h, w])   # active area
        self.add_tag(0xc61f, [4,4])         # default crop orig.
        self.add_tag(0xc620, [w-8, h-8])    # crop size (note order)

        self.add_tag(0xc62d, 0)         # Bayer split

        # color matrix 1
        a = [1,0,0, 0,1,0, 0,0,1]
        b = [1,1,1, 1,1,1, 1,1,1]
        self.add_rat_tag(0xc621, a, b)

        self.add_tag(0xC65A, 1)         # calibration - daylight

        # analog colour balance
        a,b = [1,1,1], [1,1,1]
        self.add_rat_tag(0xc627, a, b)

        # AsShotNeutral
        a,b = [1,1,1], [1,1,1]
        self.add_rat_tag(0xc628, a, b)

        self.add_tag(0xc632, [1,1])     # anti-alias
        self.add_tag(0xc65c, [1,1])     # best quality
        self.add_tag(0xc633, [1,1])     # shadow scale
        self.add_tag(0xc62a, [0,1])     # baseline exposure
        self.add_tag(0xc62b, [1,1])     # baseline noise
        self.add_tag(0xc62c, [1,1])     # baseline sharpness
        self.add_tag(0xc62e, [1,1])     # linear resp. lim
        # profile name

        tm = time.localtime()
        txt = time.strftime("%Y:%m:d %H:%M:S", tm)
        self.add_tag(0x9003, txt)
        self.add_tag(0x9004, txt)

        # image digest
        alg = hashlib.md5()
        alg.update(self.data)
        txt = alg.digest()
        hash = [ord(c) for c in txt]
        self.add_tag(0xc71c, hash)



    @staticmethod
    def convert_data(w, h, data):
        """take RGB array, apply Bayer filter and pack into byte array
           (i.e.  GR,BG)

        usage: txt = convert_data(w, h, data)
        w - image width
        h - image height
        data - sequence with RGB image samples
        txt - string to write to file
        """

        assert len(data) >= w*h, \
            "not enough image data"

        n = w*h
        buf = array('H', n*[0])

        src_step = 3        # dst_step, by definition is 1
        for jj in range(0,h,2):

            dst_ofs = w*jj
            src_ofs = src_step*w*jj

            # even row, apply GR pattern
            for kk in range(0,w,2):
                buf[dst_ofs + 0] = data[src_ofs + 1]
                buf[dst_ofs + 1] = data[src_ofs + src_step + 0]
                dst_ofs += 2
                src_ofs += 2*src_step

            # odd row, ally BG pattern
            for kk in range(0,w,2):
                buf[dst_ofs + 0] = data[src_ofs + 2]
                buf[dst_ofs + 1] = data[src_ofs + src_step + 1]
                dst_ofs += 2
                src_ofs += 2*src_step

        mn, mx = min(buf), max(buf)

        if sys.byteorder == 'little':
            buf.byteswap()

        return buf.tostring(),mn,mx
