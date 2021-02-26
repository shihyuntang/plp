import functions.make_AB_recipe as make_AB_recipe
import functions.run_IGRINS as run_IGRINS
import sys, os, argparse
import numpy as np






if __name__ == "__main__":
    print('Step 1...')

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

    if not os.path.isdir('./final_A_B_spec'):
        os.mkdir('./final_A_B_spec')

    if not os.path.isdir('./run_sh'):
        os.mkdir('./run_sh')

    if not os.path.isdir('./recipes'):
        os.mkdir('./recipes')

    # Making Recipes -----------------------------------------------------------

    new_tar_list = os.listdir('./recipes/{}_recipes'.format(args.targname.replace(' ','')))
    target_have = np.sort([ int(dump[:8]) for dump in new_tar_list if dump[-1]=='p'])

    tenn = ''
    for iii in target_have:
        tenn = tenn + str(iii) + ' '
    print('-------------------------------------')
    print('process dates:\n', tenn)


    # Make Recipes for seperated A/B/AB ----------------------------------------
    target_have = make_AB_recipe.make_AB_recipe(args.targname, target_have)

    # Make .sh file and run IGRINS ---------------------------------------------
    run_IGRINS.make_sh(args.targname, target_have, args.Nthreads, args)
    # run igrins...
    print('Step 2 Ended, please run --> bash {0:s}_run_igrins.sh manually'.format(args.targname.replace(' ','')))
    #os.popen('bash {0:s}_run_igrins.sh'.format(args.targname.replace(' ','')))
