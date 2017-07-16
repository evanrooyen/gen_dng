# -*- coding: utf8 -*-
#
# Write minimal DNG
#

import sys, getopt, os.path
from array import array
from lraw import ltiff, ldng


def gen_RGB_checkerboard(w, h, nrow=3, ncol=5, mn=1, mx=255):
    """simple gray-scale block image for testing

    usage: gen_RGB_checker(w, h, nrow=3, ncol=5, mn=1, mx=255)
    """

    npix = 3*w*h
    data = array('H')

    scl = float(mx - mn)/float(w+h)

    h_row = h/nrow
    w_col = w/ncol
    for jj in range(h):
        row = jj/h_row
        for kk in range(w):
            col = kk/w_col

            x = int(scl * (jj + kk))
            p = (row ^ col) & 1
            #c = x + mn
            c = x + mn if p == 0 else mx - x

            data.append(c)
            data.append(c)
            data.append(c)

    return data


def gen_test_tiff(w, h, data, fname):
    "write test TIFF image from RGB data"

    img = ltiff.RGB_Image()
    img.set_data(w, h, data)
    img.set_model('gen_dng', 'test-tiff')

    _fname, _ext = os.path.splitext(fname)
    tif = ltiff.TIFF()
    tif.add_image(img)
    tif.write(_fname + '.tif')

# ---------------------------------------------------------------------
def usage(msg):
    txt = ( \
        "usage: gen_dng [--test=<name>] [--tiff] <src-tif> <dst-dng>",
        "--test : generate test image internally",
        "         <name> : checker",
        "--tiff : output data as tiff file, as well as DNG"
        "")

    print ">> gen_dng.py:", msg
    for l in txt:
        print ">>",l
    sys.exit(1)


def cli_bits():
    opt_txt = 'v'
    long_opt = ('test=', 'tiff')
    options, args = getopt.getopt(sys.argv[1:], opt_txt, long_opt)

    verbose = False
    test = None
    tiff = False
    for o,a in options:
        if o == '-v':
            verbose = True
        if o == '--test':
            test = a
        if o == '--tiff':
            tiff = True

    if len(args) != 2:
        usage("unexpected no. of args")
    src = args[0]
    dst = args[1]

    return src, dst, verbose, test, tiff


if __name__ == "__main__":

    src_fname, dst_fname, verbose, test, otiff = cli_bits()


    # prepare test image internally, for reference
    if test is None:
        # load source RGB data from tiff file
        print ">> not implemented"
        sys.exit(1)
    else:
        # internal test image
        w = 4*146
        h = 3*146
        if test == "checker":
            data = gen_RGB_checkerboard(w, h, nrow=3, ncol=4, 
                mn=990, mx=30000)

    if otiff:
        gen_test_tiff(w, h, data, dst_fname)

    # build DNG image
    img = ldng.DNG_Image()
    img.set_data(w, h, data)
    img.set_model('gen_dng', 'test-conv')

    # and tiff container
    tif = ltiff.TIFF()
    tif.add_image(img)
    tif.write(dst_fname)

