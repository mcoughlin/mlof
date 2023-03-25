#!/usr/bin/env python

"""
.. module:: filter_wheel
    :platform: unix
    :synopsis: module for communicating with the filter wheel instrument of cbp

.. codeauthor:: Michael Coughlin, Eric Coughlin
"""

import serial, sys, time, glob, struct
import optparse
import numpy as np
import os
from atik_filter_wheel import AtikFilterWheel as FilterWheel


def parse_commandline():
    """
    Parse the options given on the command-line.
    """
    parser = optparse.OptionParser()

    parser.add_option("-f","--filter",default=0,type=int)
    parser.add_option("--doPosition", action="store_true",default=False)
    parser.add_option("--doGetPosition", action="store_true",default=False)

    opts, args = parser.parse_args()

    return opts


def main(runtype = "position", filter = 0):

    fws = FilterWheel()
    fws.connect(0)

    if runtype == "position":
        number_of_filters = fws.get_number_of_filters()
        if filter > number_of_filters:
            raise ValueError(f'{filter} must be <= {number_of_filters}')
        fws.set_position(filter)

    elif runtype == "getposition":
        position = fws.get_position()
        print(position)

if __name__ == "__main__":

    # Parse command line
    opts = parse_commandline()

    if opts.doPosition:
        main(runtype="position", filter=opts.filter)
    if opts.doGetPosition:
        main(runtype="getposition")
