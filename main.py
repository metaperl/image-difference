#!/usr/bin/env python


# core
import math
import os
import sys
from itertools import izip

# 3rd party
from PIL import Image, ImageChops
import distance
import pathlib
import ssim
import argh


def _dhash(image, hash_size=8):
    # Grayscale and shrink the image in one step.
    image = image.convert('L').resize(
        (hash_size + 1, hash_size),
        Image.ANTIALIAS,
    )

    pixels = list(image.getdata())

    # Compare adjacent pixels.
    difference = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = image.getpixel((col, row))
            pixel_right = image.getpixel((col + 1, row))
            difference.append(pixel_left > pixel_right)

    # Convert the binary array to a hexadecimal string.
    decimal_value = 0
    hex_string = []
    for index, value in enumerate(difference):
        if value:
            decimal_value += 2 ** (index % 8)
        if (index % 8) == 7:
            hex_string.append(hex(decimal_value)[2:].rjust(2, '0'))
            decimal_value = 0

    return ''.join(hex_string)


# http://blog.iconfinder.com/detecting-duplicate-images-using-python/
def dhash(image1, image2):
    i1 = Image.open(image1)
    i2 = Image.open(image2)

    h1 = _dhash(i1)
    h2 = _dhash(i2)

    return distance.hamming(h1, h2)


# https://pypi.python.org/pypi/pyssim
def _ssim(image1, image2):
    i1 = Image.open(image1)
    i2 = Image.open(image2)

    return ssim.compute_ssim(i1, i2)


# http://rosettacode.org/wiki/Percentage_difference_between_images#Python
def rosetta(image1, image2):
    i1 = Image.open(image1)
    i2 = Image.open(image2)
    assert i1.mode == i2.mode, "Different kinds of images."
    assert i1.size == i2.size, "Different sizes."

    pairs = izip(i1.getdata(), i2.getdata())
    if len(i1.getbands()) == 1:
        # for gray-scale jpegs
        dif = sum(abs(p1 - p2) for p1, p2 in pairs)
    else:
        dif = sum(abs(c1 - c2) for p1, p2 in pairs for c1, c2 in zip(p1, p2))

    ncomponents = i1.size[0] * i1.size[1] * 3
    retval = (dif / 255.0 * 100) / ncomponents
    return retval


# http://stackoverflow.com/questions/189943/how-can-i-quantify-difference-between-two-images
# https://gist.github.com/astanin/626356
def manhattan(image1, image2):
    import compare
    return compare.manhattan(image1, image2)


def zero_norm(image1, image2):
    import compare
    return compare.zero_norm(image1, image2)


# PIL
# http://effbot.org/zone/pil-comparing-images.htm
import math, operator

def rmsdiff(im1, im2):
    "Calculate the root-mean-square difference between two images"

    h = ImageChops.difference(im1, im2).histogram()

    # calculate rms
    return math.sqrt(reduce(operator.add,
        map(lambda h, i: h*(i**2), h, range(256))
    ) / (float(im1.size[0]) * im1.size[1]))

def chops(image1, image2):
    im1 = Image.open(image1)
    im2 = Image.open(image2)

    return rmsdiff(im1, im2)


def main(image_set_number, dhashf=False, ssimf=False, rosettaf=False, manhattanf=False, zeronormf=False, chopsf=False):
    dispatch = dict(dhash=dhash, ssim=_ssim, rosetta=rosetta, manhattan=manhattan, zero_norm=zero_norm, chops=chops)

    if dhashf: f = dispatch['dhash']
    if ssimf: f = dispatch['ssim']
    if rosettaf: f = dispatch['rosetta']
    if manhattanf: f = dispatch['manhattan']
    if zeronormf: f = dispatch['zero_norm']
    if chopsf: f = dispatch['chops']

    p = pathlib.Path("set/{0}".format(image_set_number))
    os.chdir(str(p))

    golden_image = 'image_to_match.gif'

    correct = {
        '1' : 1,
        '2' : 1,
        '3' : 0,
        '4' : 3
    }

    print "For image set {0}, the correct match is IMG-{1}.png".format(image_set_number, correct[image_set_number])

    for i in xrange(0, 4):
        i = "IMG-{0}.png".format(i)
        d = f(golden_image, i)
        print "{0}: {1}".format(i, d)


if __name__ == '__main__':
    argh.dispatch_command(main)
