import funcitons.make_AB_recipe as make_AB_recipe
import sys, os, argparse
import numpy as np
from astropy.table import Table
from astropy.io import fits




if __name__ == "__main__":
    print('Step 2...')

    parser = argparse.ArgumentParser(
                                     prog        = 'igrins plp v2.2 modified for IGRINS RV, Spectra Radial Velocity Pipeline',
                                     description = '''
                                     These code, main_step1 and 2, helps user to make input fits files for the IGRINS_RV code.
                                     ''',
                                     epilog = "Contact authors: asa.stahl@rice.edu; sytang@lowell.edu")
    parser.add_argument("targname",                          action="store",
                        help="Enter your *target name, should be the same as in the recipe", type=str)
    parser.add_argument('-mode',       dest="mode",         action="store",
                        help="plp extraction-mode, optimal OR simple. The default is optimal",
                        type=str,   default='optimal' )
    parser.add_argument('-c',       dest="Nthreads",         action="store",
                        help="Numbers of run_bash gnerate, i.e., numbers of cpu (threads) to use, default is 1",
                        type=int,   default=int(1) )

    args = parser.parse_args()
    indata_dir = './indata/'

    # Making Recipes -----------------------------------------------------------
    #target_have = make_recipe.check_obs_dates(args.targname, indata_dir)
    new_tar_list = os.listdir('./recipes/{}_recipes'.format(args.targname.replace(' ','')))
    target_have = np.sort([ int(dump[:8]) for dump in new_tar_list if dump[-1]=='p'])

    tar_night_num = []
    for i in target_have:
        temp = Table.read( './recipes/{}_recipes/{}.recipes.tmp'.format(args.targname.replace(' ',''), i), format='ascii' )
        for j in temp['GROUP1'][temp['OBJNAME'] == '{}'.format(args.targname)]:
            tar_night_num.append('{}_{:04d}'.format(i, int(j) ))

    target_have = tar_night_num
    tenn = ''
    for iii in target_have:
        tenn = tenn + str(iii) + ' '
    print('-------------------------------------')
    print('process dates:\n', tenn)

    make_AB_recipe.move_data_split(args.targname, target_have, args)


    print('-------------------------------------')
    print('Now overwrite the fits header from RAW to get the right JD time for each nodding...\n')
    #---- correcting the fits header
    target = args.targname.replace(' ','')


    if args.mode.lower()=='optimal':
        Nextend = ''
    elif args.mode.lower() == 'simple':
        Nextend = '_simple'

    end_dir   = f'./final_A_B_spec/{target}{Nextend}/'
    end_dates = [i for i in os.listdir(end_dir) if i[:2]=='20']

    # items in header need to be copied
    DCT_list = ['EXPTIME','TEMP-DET','TEMP-GRA','BAND','FRMTYPE','UTDATE','DATE-OBS','DATE-END','UT-OBS','UT-END',
                           'JD-OBS','JD-END','MJD-OBS','TELRA','TELDEC','USERRA','USERDEC','USEREPOC','FOCUSVAL','AMSTART','AMEND','HASTART','HAEND',
                           'LSTSTART','LSTEND','ZDSTART','ZDEND','PASTART','PAEND','BARPRESS','AIRTEMP','HUMIDITY','DEWPOINT','GAIN','NSAMP','RDNOISE',
                           'DATE','ACQTIME','ACQTIME1','ACQTYPE','UNITS']

    McD_list = ['DATE','ACQTIME','ACQTIME1','ACQTYPE','UNITS','EXPMODE','NRESETS','FRMTIME','EXPTIME','DATAMODE','DATLEVEL','EPOCH','OBJECT','OBJTYPE','FRMNAME',
                'UTDATE','DATE-OBS','DATE-END','MJD-OBS','UTSTART','UTEND','OBSID','OBSGROUP','OBSTOT','TEL_PA','OBSERVAT','FOCUS','RATEL','DECTEL','AMSTART','AMEND',
                'HASTART','ZDSTART','HAEND','ZDEND','AIRTEMP','BARPRESS','DEWPOINT','DOMETEMP','HUMIDITY','GAIN','RDNOISE','TEMP_2','TEMP_GR','VACUUM','PIXSCALE',
                'BAND','FILTER','JD-OBS','JD-END']

    GeminiS_list = [ 'OBSERVAT', 'TELESCOP', 'INSTRUME', 'DETECTOR', 'TIMESYS', 'OBSERVER', 'OBJECT', 'PROGID', 'GEMPRID', 'EXPTIME', 'TEMP-DET', 'TEMP-GRA', 'BAND', 'OBJTYPE',
                     'FRMTYPE', 'UTDATE', 'DATE-OBS', 'DATE-END', 'UT-OBS', 'UT-END', 'JD-OBS', 'JD-END', 'MJD-OBS', 'TELPA', 'RADECSYS', 'TELRA', 'TELDEC', 'TELEPOCH',
                     'OBJRA', 'OBJDEC', 'OBJEPOCH', 'USERRA', 'USERDEC', 'USEREPOC', 'FOCUSVAL', 'AUTOGUID', 'AMSTART', 'AMEND', 'HASTART', 'HAEND', 'LSTSTART', 'LSTEND',
                     'ZDSTART', 'ZDEND', 'PASTART', 'PAEND', 'BARPRESS', 'AIRTEMP', 'HUMIDITY', 'DEWPOINT', 'GAIN', 'NSAMP', 'RDNOISE']

    for dd in end_dates:
        for nod in ['A', 'B']:
            AB_subdir = f'./final_A_B_spec/{target}{Nextend}/{dd}/{nod}/'
            AB_subs = [i for i in os.listdir(AB_subdir) if i[:2]=='SD']

            for subAB in AB_subs:
                band = subAB[3]
                tag  = subAB[14:18]

                h_end = fits.open(f'./final_A_B_spec/{target}{Nextend}/{dd}/{nod}/{subAB}')
                end_keys = list(h_end[0].header.keys())

                h_raw = fits.open(f'./indata/{dd[:8]}/SDC{band}_{dd[:8]}_{tag}.fits')
                raw_keys = list(h_raw[0].header.keys())
                #-------------------------------------------------------------

                if h_end[0].header['OBSERVAT'].lower() == 'lowell observatory':
                    replace_list = DCT_list

                elif (h_end[0].header['OBSERVAT'].lower() == 'mcdonald observatory') or (h_end[0].header['OBSERVAT'].lower()  == 'mcdonald'):
                    replace_list = McD_list

                elif (h_end[0].header['OBSERVAT'].lower() == 'gemini observatory'):
                    if (h_end[0].header['TELESCOP'].lower() == 'gemini south'):
                        replace_list = GeminiS_list

                else:
                    sys.exit(f'Oops, cannot deal with {h_end[0].header["OBSERVAT"].lower()}')
                #-------------------------------------------------------------

                for kk in replace_list:
                    if kk in raw_keys:
                        h_end[0].header[kk] = h_raw[0].header[kk]

                h_end.writeto(f'./final_A_B_spec/{target}{Nextend}/{dd}/{nod}/{subAB}', overwrite=True)

    print('\n')
    print('Step 2 Ended. You are now ready for running IGRINS RV')
    print('Please copy the reduced 1D spectra target folder under "./final_A_B_spec" to the "input" folder in the "igrins_rv-master"')
