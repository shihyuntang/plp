import glob
import numpy as np
import sys, os
import pandas as pd
import re

from astropy.io import fits
from shutil import copyfile

pwd = os.getcwd()


def make_AB_recipe(target_n, utdates):

    indata          = pwd + '/indata/{0:8d}/'
    indata_file     = indata + 'SDC{1:s}_{0:8d}_{2:04d}.fits'

    recipe_fh        = pwd + '/recipes/' + target_n.replace(' ','') + '_recipes/{0:8d}.recipes.tmp'
    new_recipe_fh1   = pwd + '/recipes/' + target_n.replace(' ','') + '_recipes/{0:8d}.recipes'

    # plp read recipes folder
    new_recipe_fh2   = pwd + '/recipe_logs/{0:8d}.recipes'

    # new printout in the recipes
    a0std_str  = '{:s}, STD, {:d}, 1, {:f}, A0V_AB, {:02d} {:02d}, {:s} {:s}\n'
    target_str = '{:s}, TAR, {:d}, 1, {:f}, STELLAR_AB, {:02d} {:02d}, {:s} {:s}\n'

    print('-------------------------------------')
    print('Making A/B/AB recipes under plp read folder: ./recipe_log')

    print('Clearing dir ./recipe_log/ ')
    os.system('rm ./recipe_logs/*' )
    print('done')

    # print('Clearing dir ./outdata/ ')
    # os.system('rm ./outdata/*' )
    # print('done')

    # make a copy of .recipes.temp to .recipes
    for i in utdates:
        # os.system("cp " + recipe_fh.format(i) + " " + new_recipe_fh1.format(i) )
        # remove origin ABBA rows
        remove_rows = ['STELLAR_AB'] # only do target for seperate # , 'A0V_AB'
        with open( recipe_fh.format(i) ) as oldfile, open( new_recipe_fh1.format(i), 'w') as newfile:
            for line in oldfile:
                if not any(remove_row in line for remove_row in remove_rows):
                    newfile.write(line)

    # making A/B/AB recipe
    for temp, utdate in enumerate(utdates, start=1):
        print('\r', 'processing: {}, {:.2f}% {}/{}'.format(utdate, 100*temp/len(utdates), temp, len(utdates)), end=" ")

        # read in .recipes.temp
        recipe  = pd.read_csv(recipe_fh.format(utdate), comment='#')

        # extract science & A0 standard star
        science = recipe[recipe['OBJNAME'].str.contains(target_n, regex=True, flags=re.IGNORECASE)]
        A0std   = recipe[recipe[' OBJTYPE'].str.contains('STD', regex=True, flags=re.IGNORECASE)]

        if len(science) == 0:
            sys.exit(f'\nERROR! CANNOT FIND {target_n} IN RECIPE FILE, QUITE. CHECK IF THERE IS A "SPACE" MISSING.')

#-------- STD ------------------------------------------
        # for jj, x in A0std.iterrows():
        #     # extract the nodding sequences (e.g., ABBA)
        #     _frames = np.array( x[' FRAMETYPES'].strip().split(' ') )
        #     # extract the observation IDs for each nodding
        #     _ids    = [int(y) for y in x[' OBSIDS'].strip().split(' ')]
        #
        #     # check if A nodding's number match the B's
        #     if np.where(_frames=='A')[0].size != np.where(_frames=='B')[0].size:
        #         sys.exit(f"ERROR! For STD, A nodding sequence's number must match B's!!!")
        #
        #     # grouping AB sets: e.g.,  frames = [('A', 'B'), ('B', 'A'), ('A', 'B'), ('B', 'A')]
        #     frames  = list(zip(_frames[::2], _frames[1::2]))
        #     ids     = list(zip(_ids[::2], _ids[1::2]))
        #
        #     for kk, ff in zip(ids, frames):
        #         # write (append) new rows in the .recipes file
        #         with open(new_recipe_fh1.format(utdate), 'a+') as fh:
        #             #               tar_name       exp_time                 ----ids----   --frames--
        #             # target_str = '{:s}, TAR, 1, 1, {:f}, STELLAR_AB,     {:02d} {:02d}, {:s} {:s}\n'
        #             fh.write(a0std_str.format(x['OBJNAME'], kk[0], x[' EXPTIME'], kk[0], kk[1], ff[0], ff[1]))

#-------- science target--------------------------------
        for jj, x in science.iterrows():
            # extract the nodding sequences (e.g., ABBA)
            _frames = np.array( x[' FRAMETYPES'].strip().split(' ') )
            # extract the observation IDs for each nodding
            _ids    = [int(y) for y in x[' OBSIDS'].strip().split(' ')]

            # check if A nodding's number match the B's
            if np.where(_frames=='A')[0].size != np.where(_frames=='B')[0].size:
                print('####################################')
                print('ERROR!! number of the A/B nodding in night {} do not match'.format(utdate))
                print('Remove night {} from following process'.format(utdate))
                print('####################################')
                utdates = np.delete(utdates, temp-1)
                break

            # grouping AB sets: e.g.,  frames = [('A', 'B'), ('B', 'A'), ('A', 'B'), ('B', 'A')]
            frames  = list(zip(_frames[::2], _frames[1::2]))
            ids     = list(zip(_ids[::2], _ids[1::2]))

            for kk, ff in zip(ids, frames):
                # write (append) new rows in the .recipes file
                with open(new_recipe_fh1.format(utdate), 'a+') as fh:
                    #               tar_name       exp_time                 ----ids----   --frames--
                    # target_str = '{:s}, TAR, 1, 1, {:f}, STELLAR_AB,     {:02d} {:02d}, {:s} {:s}\n'
                    fh.write(target_str.format(x['OBJNAME'], kk[0], x[' EXPTIME'], kk[0], kk[1], ff[0], ff[1]))

    # copy the .recipes to the plp read dir
    for i in utdates:
        os.system("cp " + new_recipe_fh1.format(i) + " " + new_recipe_fh2.format(i) )

    return utdates

############################################################################################

def mkdir(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def move_data(target_n, utdates, args):
    # plp outdata dir AB
    # in_spec_fh  = pwd + '/outdata/{:d}/SDC{:s}_{:d}_{:04d}.spec.fits'
    # in_sn_fh    = pwd + '/outdata/{:d}/SDC{:s}_{:d}_{:04d}.sn.fits'
    # plp outdata dir A/B
    in_spec_fhab  = pwd + '/outdata/{:d}/SDC{:s}_{:d}_{:04d}_{:s}.spec.fits'
    in_sn_fhab    = pwd + '/outdata/{:d}/SDC{:s}_{:d}_{:04d}_{:s}.sn.fits'

    if args.mode.lower()=='optimal':
        Nextend = ''
    elif args.mode.lower() == 'simple':
        Nextend = '_simple'
    # final spec store dir for TAR
    out_spec_fh_tar = './final_A_B_spec/{:s}{:s}/{:d}/{:s}/SDC{:s}_{:d}_{:04d}.spec.fits'
    out_sn_fh_tar   = './final_A_B_spec/{:s}{:s}/{:d}/{:s}/SDC{:s}_{:d}_{:04d}.sn.fits'

    # final spec store dir for STD
    out_spec_fh_std = './final_A_B_spec/{:s}{:s}/std/{:d}/{:s}/SDC{:s}_{:d}_{:04d}.spec.fits'
    out_sn_fh_std   = './final_A_B_spec/{:s}{:s}/std/{:d}/{:s}/SDC{:s}_{:d}_{:04d}.sn.fits'

    # new_recipe_fh_new   = pwd + '/recipe_logs/' + '{0:8d}.recipes'
    temp_recipe_fh      = pwd + '/recipes/' + target_n.replace(' ','') + '_recipes/{0:8d}.recipes.tmp'

    for jj, ut in enumerate(utdates):
        print("{:d}".format(ut))

        recipe  = pd.read_csv(temp_recipe_fh.format(ut), comment='#')
        science = recipe[recipe['OBJNAME'].str.contains(target_n)]
        science = science.reset_index()

        A0std   = recipe[recipe[' OBJTYPE'].str.contains('STD')]

        # make final spec store dir TAR
        # mkdir("./final_A_B_spec/{:s}/{:d}/AB/".format(target_n.replace(' ', ''), ut))
        mkdir("./final_A_B_spec/{:s}{:s}/{:d}/A/".format( target_n.replace(' ', ''), Nextend, ut))
        mkdir("./final_A_B_spec/{:s}{:s}/{:d}/B/".format( target_n.replace(' ', ''), Nextend, ut))

        # make final spec store dir STD
        # mkdir("./final_A_B_spec/{:s}/std/{:d}/AB/".format(target_n.replace(' ', ''), ut))
        if args.mode.lower() == 'simple':
            mkdir("./final_A_B_spec/{:s}{:s}/std/{:d}/AB/".format( target_n.replace(' ', ''), Nextend, ut))

        mkdir("./final_A_B_spec/{:s}{:s}/std/{:d}/A/".format( target_n.replace(' ', ''), Nextend, ut))
        mkdir("./final_A_B_spec/{:s}{:s}/std/{:d}/B/".format( target_n.replace(' ', ''), Nextend, ut))

        # base on the info. in .recipes file to move each spec to the right A or B folder
#-------- science target--------------------------------
        for kk, x in science.iterrows():
            _frames = x[' FRAMETYPES'].strip().split(' ')
            _ids    = [int(y) for y in x[' OBSIDS'].strip().split(' ')]

            ids     = list(zip(_ids[::2], _ids[1::2]))
            frames  = list(zip(_frames[::2], _frames[1::2]))

            for kk, ff in zip(ids, frames):
                    for b in ['H', 'K']:
                        # copy to AB folder
                        # copyfile(in_spec_fh.format(ut, b, ut, kk[0]), out_spec_fh_tar.format(target_n.replace(' ',''), ut, 'AB', b, ut, kk[0]))
                        # copyfile(in_sn_fh.format(ut, b, ut, kk[0]),   out_sn_fh_tar.format(target_n.replace(' ',''), ut, 'AB', b, ut, kk[0]))
                        # copy to A or B folder
                        copyfile(in_spec_fhab.format(ut, b, ut, kk[0], ff[0]), out_spec_fh_tar.format(target_n.replace(' ',''), Nextend, ut, ff[0], b, ut, kk[0]))
                        copyfile(in_sn_fhab.format(ut, b, ut, kk[0], ff[0]),   out_sn_fh_tar.format(target_n.replace(' ',''), Nextend, ut, ff[0], b, ut, kk[0]))

                        copyfile(in_spec_fhab.format(ut, b, ut, kk[0], ff[1]), out_spec_fh_tar.format(target_n.replace(' ',''), Nextend, ut, ff[1], b, ut, kk[1]))
                        copyfile(in_sn_fhab.format(ut, b, ut, kk[0], ff[1]),   out_sn_fh_tar.format(target_n.replace(' ',''), Nextend, ut, ff[1], b, ut, kk[1]))
                # out_spec_fh_tar = './final_A_B_spec/{:s}/{:d}/{:s}/SDC{:s}_{:d}_{:04d}.spec.fits'

#-------- STD ------------------------------------------
        for kk, x in A0std.iterrows():
            _frames = x[' FRAMETYPES'].strip().split(' ')
            _ids    = [int(y) for y in x[' OBSIDS'].strip().split(' ')]

            ids     = list(zip(_ids[::2], _ids[1::2]))
            frames  = list(zip(_frames[::2], _frames[1::2]))

            # only copy one set of A B, the first A and B (cause ABBA's A combinded spec called with first A's ID)
            kk = ids[0]
            ff = frames[0]

            # for kk, ff in zip(ids, frames):
            #     if kk[0] in _ids: # check only copy one set of A B
            for b in ['H', 'K']:
            # copy to AB folder
            # copyfile(in_spec_fh.format(ut, b, ut, kk[0]), out_spec_fh_std.format(target_n.replace(' ',''), ut, 'AB', b, ut, kk[0]))
            # copyfile(in_sn_fh.format(ut, b, ut, kk[0]),   out_sn_fh_std.format(target_n.replace(' ',''), ut, 'AB', b, ut, kk[0]))
            # copy to A or B folder
                if args.mode.lower() == 'simple':
                    copyfile(in_spec_fhab.format(ut, b, ut, kk[0], 'AB'), out_spec_fh_std.format(target_n.replace(' ',''), Nextend, ut, 'AB', b, ut, kk[0]))
                    copyfile(in_sn_fhab.format(ut, b, ut, kk[0], 'AB'),   out_sn_fh_std.format(target_n.replace(' ',''), Nextend, ut, 'AB', b, ut, kk[0]))

                copyfile(in_spec_fhab.format(ut, b, ut, kk[0], ff[0]), out_spec_fh_std.format(target_n.replace(' ',''), Nextend, ut, ff[0], b, ut, kk[0]))
                copyfile(in_sn_fhab.format(ut, b, ut, kk[0], ff[0]),   out_sn_fh_std.format(target_n.replace(' ',''), Nextend, ut, ff[0], b, ut, kk[0]))

                copyfile(in_spec_fhab.format(ut, b, ut, kk[0], ff[1]), out_spec_fh_std.format(target_n.replace(' ',''), Nextend, ut, ff[1], b, ut, kk[1]))
                copyfile(in_sn_fhab.format(ut, b, ut, kk[0], ff[1]),   out_sn_fh_std.format(target_n.replace(' ',''), Nextend, ut, ff[1], b, ut, kk[1]))



######################

def move_data_split(target_n, utdates, args):
    # plp outdata dir AB
    # in_spec_fh  = pwd + '/outdata/{:d}/SDC{:s}_{:d}_{:04d}.spec.fits'
    # in_sn_fh    = pwd + '/outdata/{:d}/SDC{:s}_{:d}_{:04d}.sn.fits'
    # plp outdata dir A/B
    in_spec_fhab  = pwd + '/outdata/{:d}/SDC{:s}_{:d}_{:04d}_{:s}.spec.fits'
    in_sn_fhab    = pwd + '/outdata/{:d}/SDC{:s}_{:d}_{:04d}_{:s}.sn.fits'

    if args.mode.lower()=='optimal':
        Nextend = ''
    elif args.mode.lower() == 'simple':
        Nextend = '_simple'
    # final spec store dir for TAR
    out_spec_fh_tar = './final_A_B_spec/{:s}{:s}/{:s}/{:s}/SDC{:s}_{:d}_{:04d}.spec.fits'
    out_sn_fh_tar   = './final_A_B_spec/{:s}{:s}/{:s}/{:s}/SDC{:s}_{:d}_{:04d}.sn.fits'

    # final spec store dir for STD
    out_spec_fh_std = './final_A_B_spec/{:s}{:s}/std/{:d}/{:s}/SDC{:s}_{:d}_{:04d}.spec.fits'
    out_sn_fh_std   = './final_A_B_spec/{:s}{:s}/std/{:d}/{:s}/SDC{:s}_{:d}_{:04d}.sn.fits'

    # new_recipe_fh_new   = pwd + '/recipe_logs/' + '{0:8d}.recipes'
    temp_recipe_fh      = pwd + '/recipes/' + target_n.replace(' ','') + '_recipes/{0:8d}.recipes.tmp'

    for jj, ut in enumerate(utdates):
        print("{}".format(ut))

        recipe  = pd.read_csv(temp_recipe_fh.format( int(ut[:8]) ), comment='#')
        science = recipe[recipe['OBJNAME'].str.contains(target_n)]
        science = science.reset_index()

        A0std   = recipe[recipe[' OBJTYPE'].str.contains('STD')]

        # make final spec store dir TAR
        # mkdir("./final_A_B_spec/{:s}/{:s}/AB/".format(target_n.replace(' ', ''), ut))
        mkdir("./final_A_B_spec/{:s}{:s}/{:s}/A/".format( target_n.replace(' ', ''), Nextend, ut))
        mkdir("./final_A_B_spec/{:s}{:s}/{:s}/B/".format( target_n.replace(' ', ''), Nextend, ut))

        # make final spec store dir STD
        # mkdir("./final_A_B_spec/{:s}/std/{:d}/AB/".format(target_n.replace(' ', ''), int(ut[:8]) ))
        if args.mode.lower() == 'simple':
            mkdir("./final_A_B_spec/{:s}{:s}/std/{:d}/AB/".format( target_n.replace(' ', ''), Nextend, int(ut[:8]) ))

        mkdir("./final_A_B_spec/{:s}{:s}/std/{:d}/A/".format( target_n.replace(' ', ''), Nextend, int(ut[:8]) ))
        mkdir("./final_A_B_spec/{:s}{:s}/std/{:d}/B/".format( target_n.replace(' ', ''), Nextend, int(ut[:8]) ))

        # base on the info. in .recipes file to move each spec to the right A or B folder
#-------- science target--------------------------------
        for kk, x in science.iterrows():
            _frames = x[' FRAMETYPES'].strip().split(' ')
            _ids    = [int(y) for y in x[' OBSIDS'].strip().split(' ')]

            ids     = list(zip(_ids[::2], _ids[1::2]))
            frames  = list(zip(_frames[::2], _frames[1::2]))

            for kk, ff in zip(ids, frames):
                if int(ut[-4:]) in _ids:
                    for b in ['H', 'K']:
                        # copy to AB folder
                        # copyfile(in_spec_fh.format(int(ut[:8]), b, int(ut[:8]), kk[0]), out_spec_fh_tar.format(target_n.replace(' ',''), ut, 'AB', b, int(ut[:8]), kk[0]))
                        # copyfile(in_sn_fh.format(  int(ut[:8]), b, int(ut[:8]), kk[0]), out_sn_fh_tar.format(  target_n.replace(' ',''), ut, 'AB', b, int(ut[:8]), kk[0]))
                        # copy to A or B folder
                        copyfile(in_spec_fhab.format(int(ut[:8]), b, int(ut[:8]), kk[0], ff[0]), out_spec_fh_tar.format(target_n.replace(' ',''), Nextend, ut, ff[0], b, int(ut[:8]), kk[0]))
                        copyfile(in_sn_fhab.format(  int(ut[:8]), b, int(ut[:8]), kk[0], ff[0]), out_sn_fh_tar.format(  target_n.replace(' ',''), Nextend, ut, ff[0], b, int(ut[:8]), kk[0]))

                        copyfile(in_spec_fhab.format(int(ut[:8]), b, int(ut[:8]), kk[0], ff[1]), out_spec_fh_tar.format(target_n.replace(' ',''), Nextend, ut, ff[1], b, int(ut[:8]), kk[1]))
                        copyfile(in_sn_fhab.format(  int(ut[:8]), b, int(ut[:8]), kk[0], ff[1]), out_sn_fh_tar.format(  target_n.replace(' ',''), Nextend, ut, ff[1], b, int(ut[:8]), kk[1]))
                # out_spec_fh_tar = './final_A_B_spec/{:s}/{:d}/{:s}/SDC{:s}_{:d}_{:04d}.spec.fits'

#-------- STD ------------------------------------------
        for kk, x in A0std.iterrows():
            _frames = x[' FRAMETYPES'].strip().split(' ')
            _ids    = [int(y) for y in x[' OBSIDS'].strip().split(' ')]

            ids     = list(zip(_ids[::2], _ids[1::2]))
            frames  = list(zip(_frames[::2], _frames[1::2]))

            # only copy one set of A B, the first A and B (cause ABBA's A combinded spec called with first A's ID)
            kk = ids[0]
            ff = frames[0]

            # for kk, ff in zip(ids, frames):
            for b in ['H', 'K']:
                    # copy to AB folder
                    # copyfile(in_spec_fh.format(int(ut[:8]), b, int(ut[:8]), kk[0]), out_spec_fh_std.format(target_n.replace(' ',''), int(ut[:8]), 'AB', b, int(ut[:8]), kk[0]))
                    # copyfile(in_sn_fh.format(  int(ut[:8]), b, int(ut[:8]), kk[0]), out_sn_fh_std.format(  target_n.replace(' ',''), int(ut[:8]), 'AB', b, int(ut[:8]), kk[0]))
                    # copy to A or B folder
                if args.mode.lower() == 'simple':
                    copyfile(in_spec_fhab.format(int(ut[:8]), b, int(ut[:8]), kk[0], 'AB'), out_spec_fh_std.format(target_n.replace(' ',''), Nextend, int(ut[:8]), 'AB', b, int(ut[:8]), kk[0]))
                    copyfile(in_sn_fhab.format(  int(ut[:8]), b, int(ut[:8]), kk[0], 'AB'), out_sn_fh_std.format(  target_n.replace(' ',''), Nextend, int(ut[:8]), 'AB', b, int(ut[:8]), kk[0]))

                copyfile(in_spec_fhab.format(int(ut[:8]), b, int(ut[:8]), kk[0], ff[0]), out_spec_fh_std.format(target_n.replace(' ',''), Nextend, int(ut[:8]), ff[0], b, int(ut[:8]), kk[0]))
                copyfile(in_sn_fhab.format(  int(ut[:8]), b, int(ut[:8]), kk[0], ff[0]), out_sn_fh_std.format(  target_n.replace(' ',''), Nextend, int(ut[:8]), ff[0], b, int(ut[:8]), kk[0]))

                copyfile(in_spec_fhab.format(int(ut[:8]), b, int(ut[:8]), kk[0], ff[1]), out_spec_fh_std.format(target_n.replace(' ',''), Nextend, int(ut[:8]), ff[1], b, int(ut[:8]), kk[1]))
                copyfile(in_sn_fhab.format(  int(ut[:8]), b, int(ut[:8]), kk[0], ff[1]), out_sn_fh_std.format(  target_n.replace(' ',''), Nextend, int(ut[:8]), ff[1], b, int(ut[:8]), kk[1]))
