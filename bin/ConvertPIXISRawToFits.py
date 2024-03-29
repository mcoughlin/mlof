import struct 
import sys 
import matplotlib.pyplot as plt 
#from cantrips import readLinesFromFile 
import numpy as np
from datetime import datetime 
from astropy.io import fits

def readLinesFromFile(file_name): 
    lines = [] 
    with open(file_name) as f: 
        lines = f.readlines()
    lines = [line.strip() for line in lines]
    return lines  

def saveDataToFitsFile(image_array, file_name, save_dir, header = 'default', overwrite = True):

    if header == 'default':
        default_file = '/Users/sasha/Documents/Harvard/physics/stubbs/skySpectrograph/calData/' + 'default.fits'
        hdul  = fits.open(default_file)
        header = hdul[0].header 
    
    #master_med_hdu = fits.PrimaryHDU(image_array.transpose(), header = header)
    master_med_hdu = fits.PrimaryHDU(image_array, header = header)
    master_med_hdul = fits.HDUList([master_med_hdu])
    master_med_hdul.writeto(save_dir + file_name, overwrite = overwrite)
    return 1

def convertRawToFits(source_file, target_file_wo_suffix, 
                     source_dir = '', target_dir = '', n_imgs = 1, 
                     img_dimen = [1024, 1024], n_unsigned_bytes = 2,
                     target_suffix = '.fits', big_endian = 0, header_elems_to_add = []):
    raw_object = open(source_dir + source_file, 'rb') 
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
    print ('header_elems_to_add = ' + str(header_elems_to_add))  
    for header_elem in header_elems_to_add: 
        header_key_str = header_elem[0]  
        new_header[header_key_str] = (header_elem[1], header_elem[2])  

    if n_imgs > 1:  
        [saveDataToFitsFile(img_arrays[i], target_file + '_' + str(i) + '.fits', target_dir, header = new_header)  
         for i in range(len(img_arrays)) ]
    else: 
        saveDataToFitsFile(img_arrays[0], target_file_wo_suffix + target_suffix, target_dir, header = new_header)

    return 1 

def BuildInitialHeader(exposure_parameter_file, target_name, exp_time, shutter_key, gain_key, exp_speed_key, focus_pos, l_start_time, l_end_time): 
    exp_time = float(exp_time.strip()) 
    shutter_key = int(shutter_key.strip())
    gain_key = int(gain_key.strip()) 
    exp_speed_key = int(exp_speed_key.strip())  
    focus_pos = float(focus_pos.strip()) 
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
    additional_header_elems = additional_header_elems + [['TARGET', 
                                                          target_name,  
                                                          "target of exposure"],
                                                         ['EXPTIME', 
                                                          exp_time / 1000.0, #exp time specified in millisecons and we want to save it in seconds in header 
                                                          "[s] exposure time"], 
                                                         ['INSTRUME', 
                                                          'OSELOTS', 
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
                                                         ['FOCUSPOS',
                                                           focus_pos, 
                                                          'Position of collimating lens (mm)'],
                                                         ['LOCSTART', 
                                                          l_start_time,  
                                                          'Start of exposure, in local (computer) time' ], 
                                                         ['LOCEND',
                                                           l_end_time, 
                                                          'End of exposure, in local (computer) time']
                                                        ]
    stored_param_key_strs = ['TEMP','STARTEXP','ENDEXP']
    stored_param_comments = ['temperature of PIXIS CCD', 'start of acquisition (GMT)', 'end of acquisition (GMT)']
    stored_param_conversion_functs = [lambda val: int(val.strip()), 
                                      lambda val: datetime.utcfromtimestamp(float(val.strip())).strftime('%Y-%m-%dT%H:%M:%SZ'), 
                                      lambda val: datetime.utcfromtimestamp(float(val.strip())).strftime('%Y-%m-%dT%H:%M:%SZ') ]
    lines = readLinesFromFile(source_dir + exposure_parameter_file) 
    for i in range(len(lines)): 
        line = lines[i] 
        additional_header_elems = additional_header_elems + [[stored_param_key_strs[i], stored_param_conversion_functs[i](lines[i]), stored_param_comments[i]]]

    return additional_header_elems 



if __name__ == "__main__":
    #print ('sys.argv[1:] = ' + str(sys.argv[1:])) 
    source_file, target_file, exposure_parameter_file, source_dir, target_dir, target_name, exp_time, shutter_key, gain_key, exp_speed_key, focus_pos, local_start_time, local_end_time = sys.argv[1:]
    additional_header_elems = BuildInitialHeader(exposure_parameter_file, target_name, exp_time, shutter_key, gain_key, exp_speed_key, focus_pos, local_start_time, local_end_time)
    
    target_suffix = '.fits'  
    #temperature_string = readLinesFromFile(source_dir + temperature_file)[0] 
    convertRawToFits(source_file, target_file, source_dir = source_dir, target_dir = target_dir, target_suffix = target_suffix, header_elems_to_add = additional_header_elems); 
    print ('Done converting file: ' + str(source_dir + source_file) + ' to file: ' + str(target_dir + target_file + target_suffix) )
     

    
