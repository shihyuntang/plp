import glob
import numpy as np
import sys, os
import pandas as pd
import re

from astropy.io import fits
from shutil import copyfile

pwd = os.getcwd()

def make_AB_recipe(target_n, target_have):

    indata          = pwd + '/indata/{0:8d}/'
    indata_file     = indata + 'SDC{1:s}_{0:8d}_{2:04d}.fits'
    recipe_fh       =  pwd + '/recipes/' + target_n.replace(' ','') + '_recipes/{0:8d}.recipes.tmp'
    new_recipe_fh1   = pwd + '/recipes/' + target_n.replace(' ','') + '_recipes/{0:8d}.recipes'

    new_recipe_fh2   = pwd + '/recipe_logs/{0:8d}.recipes'

    new_recipe_fh_old   = pwd + '/recipe_logs/' + '{0:8d}.recipes.tmp'
    new_recipe_fh_new   = pwd + '/recipe_logs/' + '{0:8d}.recipes'

    stellar_ab_str      = target_n +', TAR, 1, 1, {0:f}, STELLAR_AB, {1:02d} {2:02d}, {3:s} {4:s}\n'
    stellar_onoff_str   = target_n +', TAR, 1, 1, {0:f}, STELLAR_AB, {1:02d} {2:02d}, {3:s} {4:s}\n'
    max_ind = 1000

    print('-------------------------------------')
    print('Making A/B/AB recipes under ./recipe_log')

    print('Clearing dir ./recipe_log/ ')
    os.system('rm ./recipe_logs/*' )
    print('done')

    print('Clearing dir ./outdata/ ')
    os.system('rm -r ./outdata/*' )
    print('done')

    for i in target_have:
        # copy to ./recipe_log
        os.system("cp " + recipe_fh.format(i) + " " + new_recipe_fh1.format(i) )

    # making A/B/AB recipe
    utdates = target_have

    temp = 1
    for utdate in utdates:
        print('\r', 'processing: {}, {:.2f}% {}/{}'.format(utdate, 100*temp/len(utdates), temp, len(utdates)), end=" ")

        recipe  = pd.read_csv(new_recipe_fh1.format(utdate), comment='#')
        science = recipe[recipe['OBJNAME'].str.contains(target_n, regex=True, flags=re.IGNORECASE)]

        for jj, x in science.iterrows():
            _frames = x[' FRAMETYPES'].strip().split(' ')
            _ids    = [int(y) for y in x[' OBSIDS'].strip().split(' ')]

            if np.mod(len(_ids), 2) != 0:
                print('####################################')
                print('{} ERROR number of A/B in recipe is not even'.format(utdate))
                print('Will remove {} from following process'.format(utdate))
                print('####################################')
                target_have = np.delete(target_have, temp-1)
                break

            ids     = list(zip(_ids[::2], _ids[1::2]))
            frames  = list(zip(_frames[::2], _frames[1::2]))

            for kk in _ids: # replicate all the files
                for b in ['H', 'K']:
                    if not os.path.exists(indata_file.format(utdate, b, max_ind + kk)):
                        copyfile(indata_file.format(utdate, b, kk), indata_file.format(utdate, b, max_ind + kk))
            for kk, ff in zip(ids, frames):
                for b in ['H', 'K']:
                    try:
                        hduA = fits.open(indata_file.format(utdate, b, max_ind + kk[0]))
                        hduB = fits.open(indata_file.format(utdate, b, max_ind + kk[1]))

                        data_new = np.min([hduA[0].data, hduB[0].data], axis=0)
                        hdul = fits.PrimaryHDU(data_new, header=hduA[0].header)
                        hdul.writeto(indata_file.format(utdate, b, max_ind + kk[0] + 1000), overwrite=True)
                    except:
                        print('error occures at date {}, please check it and RE RUN main1.py'.format(utdate))
                with open(new_recipe_fh1.format(utdate), 'a+') as fh:
                    fh.write(stellar_onoff_str.format(x[' EXPTIME'], kk[0] + 1000,    kk[0] + max_ind + 1000, ff[0], ff[1]))
                    fh.write(stellar_onoff_str.format(x[' EXPTIME'], kk[1] + max_ind, kk[0] + max_ind + 1000, ff[1], ff[0]))
        temp += 1

    for i in target_have:
        os.system("cp " + new_recipe_fh1.format(i) + " " + new_recipe_fh2.format(i) )
    # New target_hav ing list
    return target_have


def mkdir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def move_data(target_n, target_have):
    utdates = target_have

    indata          = pwd + '/indata/{0:8d}/'
    indata_file     = indata + 'SDC{1:s}_{0:8d}_{2:04d}.fits'
    recipe_fh       = pwd + '/' + target_n.replace(' ','') + '_recipes/{0:8d}.recipes.tmp'
    new_recipe_fh   = pwd + '/recipe_logs/'
    new_recipe_fh_old   = pwd + '/recipe_logs/' + '{0:8d}.recipes.tmp'
    new_recipe_fh_new   = pwd + '/recipe_logs/' + '{0:8d}.recipes'


    in_spec_fh  = pwd + '/outdata/{0:d}/SDC{1:s}_{0:d}_{2:04d}.spec.fits'
    in_sn_fh    = pwd + '/outdata/{0:d}/SDC{1:s}_{0:d}_{2:04d}.sn.fits'

    out_spec_fht = './final_A_B_spec/{0:s}/{1:d}/{2:s}/SDC{3:s}_{1:d}_{4:04d}.spec.fits'
    out_sn_fht   = './final_A_B_spec/{0:s}/{1:d}/{2:s}/SDC{3:s}_{1:d}_{4:04d}.sn.fits'

    out_spec_fhs = './final_A_B_spec/{0:s}/{1:s}/{2:d}/{3:s}/SDC{4:s}_{2:d}_{5:04d}.spec.fits'
    out_sn_fhs   = './final_A_B_spec/{0:s}/{1:s}/{2:d}/{3:s}/SDC{4:s}_{2:d}_{5:04d}.sn.fits'

    new_recipe_fh_new   = pwd + '/recipe_logs/' + '{0:8d}.recipes'

    for jj, ut in enumerate(utdates):
        print("{0:d}".format(ut))

        recipe  = pd.read_csv(new_recipe_fh_new.format(ut), comment='#')
        science = recipe[recipe['OBJNAME'].str.contains(target_n)]
        science = science.reset_index()

        std     = recipe[recipe[' OBJTYPE'].str.contains('STD')]

        mkdir("./final_A_B_spec/{0:s}/{1:d}/AB/".format(target_n.replace(' ', ''), ut))
        mkdir("./final_A_B_spec/{0:s}/{1:d}/A/".format(target_n.replace(' ', ''), ut))
        mkdir("./final_A_B_spec/{0:s}/{1:d}/B/".format(target_n.replace(' ', ''), ut))
        mkdir("./final_A_B_spec/{0:s}/std/{1:d}/AB/".format(target_n.replace(' ', ''), ut))

        for kk, x in science.iterrows():
            _frames = x[' FRAMETYPES'].strip().split(' ')
            _ids = [int(y) for y in x[' OBSIDS'].strip().split(' ')]

            for b in ['H', 'K']:
                if _ids[0] < 1000:
                    try:
                        copyfile(in_spec_fh.format(ut, b, _ids[0]), out_spec_fht.format(target_n.replace(' ',''), ut, 'AB', b, _ids[0]))
                        copyfile(in_sn_fh.format(ut, b, _ids[0]), out_sn_fht.format(target_n.replace(' ',''), ut, 'AB', b, _ids[0]))
                    except:
                        print("Failed to copy: " +  in_spec_fh.format(ut, b, _ids[0]))
                        pass
                else:
                    try:
                        copyfile(in_spec_fh.format(ut, b, _ids[0]), out_spec_fht.format(target_n.replace(' ',''), ut, _frames[0], b, _ids[0]-1000))
                        copyfile(in_sn_fh.format(ut, b, _ids[0]), out_sn_fht.format(target_n.replace(' ',''), ut, _frames[0], b, _ids[0]-1000))
                    except:
                        print("Failed to copy: " + in_spec_fh.format(ut, b, _ids[0]))
                        pass
        for kk, x in std.iterrows():
            _frames = x[' FRAMETYPES'].strip().split(' ')
            _ids = [int(y) for y in x[' OBSIDS'].strip().split(' ')]
            for b in ['H', 'K']:
                try:
                    copyfile(in_spec_fh.format(ut, b, _ids[0]), out_spec_fhs.format(target_n.replace(' ',''), 'std', ut, 'AB', b, _ids[0]))
                    copyfile(in_sn_fh.format(ut, b, _ids[0]), out_sn_fhs.format(target_n.replace(' ',''), 'std', ut, 'AB', b, _ids[0]))
                except:
                    print("Failed to copy: " +  in_spec_fh.format(ut, b, _ids[0]))
                    pass
