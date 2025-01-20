import functions.make_AB_recipe as make_AB_recipe
import sys, os, argparse, ast
import numpy as np
from astropy.io import fits
# from astroquery.simbad import Simbad
from astropy.coordinates import SkyCoord, ICRS, EarthLocation
from astropy.time import Time
from astropy import units as u
from astropy.table import Table

def get_bvc(jd, obs, args):
    # ra_deg = np.array(ast.literal_eval(args.coord), dtype=float)[0]
    # de_deg = np.array(ast.literal_eval(args.coord), dtype=float)[1]
    # pmra_deg = np.array(ast.literal_eval(args.pm), dtype=float)[0]
    # pmde_deg = np.array(ast.literal_eval(args.pm), dtype=float)[1]

    if args.coord == '' or args.pm == '' or args.epoch == '':
        print('\n WARNING!!! Please give the coord, pm, and epoch info for the target to get BVC calculation.')
        print('  >>> Currently assign 0 for BVC Currently assign 0 for BVC Currently assign 0 for BVC')
        print('  >>> Currently assign 0 for BVC Currently assign 0 for BVC Currently assign 0 for BVC\n')
        return 0
    
    ra_deg = np.array(ast.literal_eval(args.coord), dtype=float)[0]
    de_deg = np.array(ast.literal_eval(args.coord), dtype=float)[1]

    pmra_deg = np.array(ast.literal_eval(args.pm), dtype=float)[0]
    pmde_deg = np.array(ast.literal_eval(args.pm), dtype=float)[1]
    
    dist_pc = float(args.dist) if args.dist != '' else None

    if dist_pc is not None:
        targ_c = SkyCoord(
            ra  =  ra_deg           *u.degree,
            dec =  de_deg           *u.degree,
            pm_ra_cosdec = pmra_deg *u.mas/u.yr,
            pm_dec       = pmde_deg *u.mas/u.yr,
            distance     = dist_pc  *u.pc,
            frame='icrs',
            obstime=args.epoch
            )
            
        new_coord = targ_c.apply_space_motion(
            new_obstime=Time(jd, format='jd'))
    else:
        targ_c = SkyCoord(
            ra  =  ra_deg           *u.degree,
            dec =  de_deg           *u.degree,
            pm_ra_cosdec = pmra_deg *u.mas/u.yr,
            pm_dec       = pmde_deg *u.mas/u.yr,
            frame='icrs',
            obstime=args.epoch
            )
        new_coord = targ_c

    if obs == 'McD':
        observatoryN = EarthLocation.of_site('McDonald Observatory')
    elif obs == 'DCT':
        observatoryN = EarthLocation.of_site('DCT')
    elif obs == 'GeminiS':
        observatoryN = EarthLocation.of_site('Gemini South')

    new_RA = new_coord.ra
    new_DE = new_coord.dec

    sc = SkyCoord(ra=new_RA, dec=new_DE, frame=ICRS)

    barycorr  = sc.radial_velocity_correction(
        obstime=Time(jd, format='jd'), 
        location=observatoryN
        )
    bvc   = barycorr.to(u.km/u.s).value
    return bvc


if __name__ == "__main__":
    print('\nStep 2...')

    parser = argparse.ArgumentParser(
                                     prog        = 'igrins plp v3.0 modified for IGRINS RV, Spectra Radial Velocity Pipeline',
                                     description = '''
                                     These code, main_step1 and 2, helps user to make input fits files for the IGRINS_RV code.
                                     ''',
                                     epilog = "Contact authors: asa.stahl@rice.edu; sytang@lowell.edu")
    parser.add_argument("targname",                          action="store",
                        help="Enter your *target name, should be the same as in the recipe", type=str)
    parser.add_argument('-mode',       dest="mode",         action="store",
                        help="plp extraction-mode, optimal OR simple. The default is optimal",
                        type=str,   default='optimal' )
    parser.add_argument(
        "-AM", dest="AM_cut", action="store",
        help="AirMass difference allowed between TAR and STD (A0) stars. \
                Default 0.3 ",
        type=str, default='0.3'
        )
    parser.add_argument(
        "-coord", dest="coord", action="store",
        help="Optional [-XX.xx,-XX.xx] deg. \
                If give, will calculate BVC base on this info.",
        type=str, default=''
        )
    parser.add_argument(
        "-pm", dest="pm", action="store",
        help="Optional [-XX.xx,-XX.xx] [mas/yr]. \
                If give, will calculate BVC base on this info.",
        type=str, default=''
        )
    parser.add_argument(
        "-epoch", dest="epoch", action="store",
        help="Target coord and pm epoch, e.g., GaiaDR2 is J2015.5, DR3 is J2016.0. \
                Must give if coord and pm are given.",
        type=str, default=''
        )
    parser.add_argument(
        "-distance", dest="dist", action="store",
        help="Target distance in pc. For a more precise coordinate calculation. \
                If not given, BVC can still be calculated.",
        type=str, default=''
        )
    # parser.add_argument('-c',       dest="Nthreads",         action="store",
    #                     help="Numbers of run_bash gnerate, i.e., numbers of cpu (threads) to use, default is 1",
    #                     type=int,   default=int(1) )

    args = parser.parse_args()
    indata_dir = './indata/'

    # Making Recipes -----------------------------------------------------------
    #target_have = make_recipe.check_obs_dates(args.targname, indata_dir)
    new_tar_list = os.listdir('./recipes/{}_recipes'.format(args.targname.replace(' ','')))
    target_have = np.sort(
        [ int(dump[:8]) for dump in new_tar_list if dump.endswith('.tmp') ])

    tenn = ''
    for iii in target_have:
        tenn = tenn + str(iii) + ' '
    print('-------------------------------------')
    print('process dates:\n', tenn)
    #target_have = np.array([20141123, 20151106, 20151108, 20151111])
    make_AB_recipe.move_data(args.targname, target_have, args)

    ###########################################################################
    print('\n-------------------------------------')
    print('Now overwrite the fits header from RAW to get the right JD time for each nodding...')
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
    
    ###########################################################################
    print('\n-------------------------------------')
    print('Also make the PrepData for IGRINS RV')
    # ---- PrepData_targ_[target name].txt ----
    # night beam tag jd facility airmass bvc
    night_box = [] 
    beam_box = []
    tag_box = [] 
    jd_box = [] 
    facility_box = [] 
    airmass_box = [] 
    bvc_box = []
    for dd in end_dates:
        for nod in ['A', 'B']:
            AB_subdir = f'./final_A_B_spec/{target}{Nextend}/{dd}/{nod}/'
            AB_subs = [
                i for i in os.listdir(AB_subdir) if i.startswith('SDCK') and i.endswith('.spec.fits')
                ]
            for subAB in AB_subs:
                # SDCK_20241220_0117.spec.fits
                tag  = subAB.split('_')[2].split('.')[0]
                _h = fits.open(f'{AB_subdir}/{subAB}')

                try:
                    jd = (float(_h[0].header['JD-OBS']) + float(_h[0].header['JD-END'])) / 2
                except KeyError:
                    l0 = []
                    for nm in ['DATE-OBS','DATE-END']:
                        tt1 = _h[0].header[nm].split('-')
                        t1 = Time(tt1[0]+'-'+tt1[1]+'-'+tt1[2]+' '+tt1[3],format='iso')
                        l0.append(t1.jd)
                    jd = np.mean(l0)
        
                if h_end[0].header['OBSERVAT'].lower() == 'lowell observatory':
                    facility = 'DCT'
                elif (h_end[0].header['OBSERVAT'].lower() == 'mcdonald observatory') or (h_end[0].header['OBSERVAT'].lower()  == 'mcdonald'):
                    facility = 'McD'
                elif (h_end[0].header['OBSERVAT'].lower() == 'gemini observatory'):
                    if (h_end[0].header['TELESCOP'].lower() == 'gemini south'):
                        facility = 'GeminiS'
                else:
                    sys.exit(f'Oops, cannot deal with {h_end[0].header["OBSERVAT"].lower()}')
                
                airmass = (float(_h[0].header['AMSTART']) + float(_h[0].header['AMEND'])) / 2
                bvc = get_bvc(jd, facility, args)

                night_box.append(dd)
                beam_box.append(nod)
                tag_box.append(tag)
                jd_box.append(jd)
                facility_box.append(facility)
                airmass_box.append(airmass)
                bvc_box.append(bvc)
    tar_prepdata = Table(
        [night_box, beam_box, tag_box, jd_box, facility_box, airmass_box, bvc_box], 
        names=('night', 'beam', 'tag', 'jd', 'facility', 'airmass', 'bvc') )
    
    # ---- PrepData_A0_[target name].txt ----
    # night tag humid temp zd press facility airmass
    night_box = [] 
    tag_box = [] 
    humid_box = []
    temp_box = []
    zd_box = []
    press_box = [] 
    facility_box = [] 
    airmass_box = [] 
    for dd in end_dates:
        for nod in ['A', 'B']:
            AB_subdir = f'./final_A_B_spec/{target}{Nextend}/std/{dd}/{nod}/'
            AB_subs = [
                i for i in os.listdir(AB_subdir) if i.startswith('SDCK') and i.endswith('.spec.fits')
                ]
            for subAB in AB_subs:
                # SDCK_20241220_0117.spec.fits
                tag  = subAB.split('_')[2].split('.')[0]
                _h = fits.open(f'{AB_subdir}/{subAB}')

                if h_end[0].header['OBSERVAT'].lower() == 'lowell observatory':
                    facility = 'DCT'
                elif (h_end[0].header['OBSERVAT'].lower() == 'mcdonald observatory') or (h_end[0].header['OBSERVAT'].lower()  == 'mcdonald'):
                    facility = 'McD'
                elif (h_end[0].header['OBSERVAT'].lower() == 'gemini observatory'):
                    if (h_end[0].header['TELESCOP'].lower() == 'gemini south'):
                        facility = 'GeminiS'
                else:
                    sys.exit(f'Oops, cannot deal with {h_end[0].header["OBSERVAT"].lower()}')
                
                airmass = (float(_h[0].header['AMSTART']) + float(_h[0].header['AMEND'])) / 2

                rel_humidity = _h[0].header['HUMIDITY']
                temp = _h[0].header['AIRTEMP']
                press = _h[0].header['BARPRESS']

                night_box.append(dd)
                tag_box.append(tag)
                try:
                    zd = (float(_h[0].header['ZDSTART']) + float(_h[0].header['ZDEND'])) / 2
                    zd_box.append(zd)
                except ValueError:
                    zd_box.append('NOINFO')
                    
                facility_box.append(facility)
                airmass_box.append(airmass)

                if facility != 'McD':
                    humid_box.append(rel_humidity)
                    temp_box.append(temp)    
                    press_box.append(press)    
                else:
                    humid_box.append('NOINFO')
                    temp_box.append('NOINFO')    
                    press_box.append('NOINFO')
                    

    A0_prepdata = Table(
        [night_box, tag_box, humid_box, temp_box, zd_box, press_box, facility_box, airmass_box], 
        names=('night', 'tag', 'humid', 'temp', 'zd', 'press', 'facility', 'airmass') )
    
    tar_prepdata['jd'].format = '.6f'
    tar_prepdata['airmass'].format = '.2f'
    tar_prepdata['bvc'].format = '10.6f'

    A0_prepdata['zd'].format = '.1f'

    if 'McD' not in facility_box:
        A0_prepdata['humid'].format = '.0f'
        A0_prepdata['temp'].format = '.0f'
        A0_prepdata['press'].format = '.0f'
        A0_prepdata['airmass'].format = '.2f'

    
    tar_prepdata.write(
        f'./final_A_B_spec/{target}{Nextend}/Prepdata_targ_{target}.txt', 
        format='ascii', overwrite=True)
    A0_prepdata.write(
        f'./final_A_B_spec/{target}{Nextend}/Prepdata_A0_{target}.txt', 
        format='ascii', overwrite=True)

    print('\nStep 2 Ended. You are now ready for running IGRINS RV')
    print('Please copy the reduced 1D spectra target folder under "./final_A_B_spec" to the "input" folder in the "igrins_rv-master"')
