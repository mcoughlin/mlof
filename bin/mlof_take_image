import os
import optparse
import struct 
import sys 
import matplotlib.pyplot as plt 
#from cantrips import readLinesFromFile 
import numpy as np
from datetime import datetime 
from astropy.io import fits
from astropy.time import Time

from subprocess import check_output

def readLinesFromFile(file_name): 
    lines = [] 
    with open(file_name) as f: 
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    return lines  

def convertRawToFits(source_file, target_file, n_imgs = 1, 
                     img_dimen = [1024, 1024], n_unsigned_bytes = 2,
                     target_suffix = '.fits', big_endian = 0, header = []):
    raw_object = open(source_file, 'rb') 
    raw_data = raw_object.read() 
    single_img_length = img_dimen[0] * img_dimen[1] * n_unsigned_bytes
    separated_data = [raw_data[i * single_img_length:(i+1) * single_img_length ] 
                      for i in range(n_imgs) ]
    #The endian-ness of the data flipped on me at least once during my time working with the camera.
    #I therefore am providing the user the opportunity to flip the endianness, if they need to
    # (once the data is moved to a fits file, then it should be stable). 
    #If you are seeing an image that looks only like noise, and the noise is escessive
    # or one with 'tearing' patterns, then you might try flipping the endian-ness here and see
    # if that helps. 
    if big_endian:
        img_fmt = '>' + str(img_dimen[0] * img_dimen[1]) + 'H' 
    else: 
        img_fmt = '<' + str(img_dimen[0] * img_dimen[1]) + 'H' 

    flat_img_arrays = [struct.unpack(img_fmt, data_set) for data_set in separated_data]
 
    img_arrays = [np.flip(np.reshape(flat_img, img_dimen),0) for flat_img in flat_img_arrays]

    new_header = fits.Header() 
    new_header['SIMPLE'] = ('T', 'Created by convertRawToFits.py')
    new_header['BITPIX'] = (n_unsigned_bytes * 8, 'number of bits per data pixel')
    new_header['NAXIS'] = (2, 'number of data axes') 
    new_header['NAXIS1'] = (1024, 'length of data axis 1') 
    new_header['NAXIS2'] = (1024, 'length of data axis 2')
    new_header['BZERO'] = (32768, 'data range offset')
    new_header['BSCALE'] = (1, 'default scaling factor')
    for header_elem in header: 
        header_key_str = header_elem[0]  
        new_header[header_key_str] = (header_elem[1], header_elem[2])  

    master_med_hdu = fits.PrimaryHDU(img_arrays[0], header = new_header)
    master_med_hdul = fits.HDUList([master_med_hdu])
    master_med_hdul.writeto(target_file, overwrite = True)


def BuildInitialHeader(args, t0=Time.now(), exposure_parameter_file=None):

    target_name = args.name
    exp_time = float(args.exposure_time)
    shutter_key = int(args.shutter)
    gain_key = int(args.gain) 
    exp_speed_key = int(args.readout_speed)  
    if exp_time < 1: 
        obs_type = 'BIAS' 
    elif shutter_key == 1: 
        obs_type = 'DARK' 
    else: 
        obs_type = 'NORMAL' 
    gain_dict = {0:4, 1:2, 2:1} 
    readnoise_dict = {0:3.0, 1:9.0}
    readout_speed_dict = {0:1.0, 1:0.2}
    fast_dict = {} 
    additional_header_elems = []
    additional_header_elems = [['TARGET', 
                                target_name,  
                                "target of exposure"],
                               ['EXPTIME', 
                                exp_time / 1000.0, #exp time specified in millisecons and we want to save it in seconds in header 
                                "[s] exposure time"], 
                               ['INSTRUME', 
                                'MLOF', 
                                'Instrument in use' ], 
                               ['OBSTYPE', 
                                obs_type,  
                                "Type of exposure (BIAS, DARK, or NORMAL) "], 
                               ['GAIN', 
                                gain_dict[gain_key],  
                                '[e-/ADU] PIXIS detector gain' ], 
                               ['RDSPEED', 
                                readout_speed_dict[exp_speed_key],  
                                "[MHz] PIXIS readout speed setting "], 
                               ['RDNOISE', 
                                readnoise_dict[exp_speed_key],  
                                '[e-] PIXIS typical rms readnoise' ], 
                               ['TIME', 
                                str(t0.jd),  
                                'Start of exposure, in local (computer) time' ], 
                               ]
    stored_param_key_strs = ['TEMP','STARTEXP','ENDEXP']
    stored_param_comments = ['temperature of PIXIS CCD', 'start of acquisition (GMT)', 'end of acquisition (GMT)']
    stored_param_conversion_functs = [lambda val: int(val.strip()), 
                                      lambda val: datetime.utcfromtimestamp(float(val.strip())).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                                      lambda val: datetime.utcfromtimestamp(float(val.strip())).strftime('%Y-%m-%dT%H:%M:%SZ') ]

    if exposure_parameter_file is not None:
        lines = readLinesFromFile(exposure_parameter_file) 
        for i in range(len(lines)): 
            line = lines[i] 
            additional_header_elems = additional_header_elems + [[stored_param_key_strs[i], stored_param_conversion_functs[i](lines[i]), stored_param_comments[i]]]

    return additional_header_elems 

def parse_commandline():
    """
    Parse the options given on the command-line.
    """
    parser = optparse.OptionParser()

    parser.add_option("-o","--output_file")
    parser.add_option("-e","--exposure_time", type=int, help="exposure time, in ms", default=0)
    parser.add_option("-n","--name", type=str, help="name of target, as it will appear in Fits header")
    parser.add_option("-s","--shutter", type=int, help="should shutter act normally, opening during exposure (0), or stay closed at all times (1)", default=0)
    parser.add_option("-g","--gain", type=int, help="Define the gain.  It can be set to 0, 1, or 2, which correspond to low, medium, or high numbers of ADUs per electron, respectively. For the PIXIS 1024R, low = (4e-/ADU), medium =(2e-/ADU), and high = (1e-/ADU).", default=0)
    parser.add_option("-r","--readout_speed", type=int, help="the readout speed.  Can be faster and noiser (1) or slower and less noisy (0).", default=0)
    parser.add_option("-t","--time", type=str)

    parser.add_option("--doTemperatureLock", action="store_true",default=False)

    opts, args = parser.parse_args()

    return opts


if __name__ == "__main__":

    # Parse command line
    args = parse_commandline()

    configure_sasha = check_output(["which", "configure_sasha"]).decode().replace("\n","")     

    source_file = args.output_file.replace("fits","raw")
    exposure_file = args.output_file.replace("fits","txt")
    filename = args.output_file.replace(".fits","") 

    outdir = "/".join(args.output_file.split("/")[:-1])
    if not outdir == "" and not os.path.isdir(outdir):
        os.makedirs(outdir)

    t0 = Time.now() 
    if args.doTemperatureLock:
        system_command = f"{configure_sasha} {args.exposure_time} 1 {args.shutter} {args.gain} {args.readout_speed} {filename} {filename} lock"
    else:
        system_command = f"{configure_sasha} {args.exposure_time} 1 {args.shutter} {args.gain} {args.readout_speed} {filename} {filename}"
    os.system(system_command)

    header = BuildInitialHeader(args, t0=t0, exposure_parameter_file=exposure_file)
    convertRawToFits(source_file, args.output_file, header = header); 
     

    
