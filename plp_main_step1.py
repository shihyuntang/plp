import sys, os, argparse, shutil

import numpy as np
from astroquery.simbad import Simbad
import pandas as pd

import functions.make_AB_recipe as make_AB_recipe
import functions.run_IGRINS as run_IGRINS



if __name__ == "__main__":
    print('\nStep 1...')

    parser = argparse.ArgumentParser(
                                     prog        = 'igrins plp v3.0 modified for IGRINS RV, IGRINS Radial Velocity Pipeline',
                                     description = '''
                                     These code, main_step1 and 2, helps user to make input fits files for the IGRINS_RV code.
                                     ''',
                                     epilog = "Contact authors: asa.stahl@rice.edu; sytang@lowell.edu")
    parser.add_argument("targname",                          action="store",
                        help="Enter your *target name, should be simbad searchable or simbad MAIN ID. Only take one target per run!", type=str)
    parser.add_argument('-mode',       dest="mode",         action="store",
                        help="plp extraction-mode, optimal OR simple. The default is optimal",
                        type=str,   default='optimal' )
    parser.add_argument('-c',       dest="Nthreads",         action="store",
                        help="Numbers of run_bash gnerate, i.e., numbers of cpu (threads) to use, default is 1",
                        type=int,   default=int(1) )

    args = parser.parse_args()
    indata_dir = './indata/'

    os.makedirs(os.path.dirname('./final_A_B_spec/'), exist_ok=True)
    os.makedirs(os.path.dirname('./run_sh/'), exist_ok=True)
    os.makedirs(os.path.dirname('./recipes/'), exist_ok=True)
    os.makedirs(os.path.dirname('./recipe_logs/'), exist_ok=True)

    # Run igr_pipe.py prepare-recipe-logs to get the recipe logs ----------------
    # -------------------------------------
    new_tar_list = os.listdir('./recipes/{}_recipes'.format(args.targname.replace(' ','')))
    target_have = np.sort(
        [ int(dump[:8]) for dump in new_tar_list if dump.endswith('.tmp') ])

    tenn = ''
    for iii in target_have:
        tenn = tenn + str(iii) + ' '
    print('-------------------------------------')
    print('Process dates:\n', tenn)


    # Make Recipes for separated A/B/AB ----------------------------------------
    target_have = make_AB_recipe.make_AB_recipe(args.targname, target_have)

    # Make .sh file and run IGRINS ---------------------------------------------
    run_IGRINS.make_sh(args.targname, target_have, args.Nthreads, args)
    # run igrins...
    print('\nStep 1 Ended, please run --> bash ./run_sh/{0:s}_run_igrinsX.sh manually'.format(args.targname.replace(' ','')))
    #os.popen('bash {0:s}_run_igrins.sh'.format(args.targname.replace(' ','')))
