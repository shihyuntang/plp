import funcitons.make_AB_recipe as make_AB_recipe
import sys, os, argparse
import numpy as np





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
    parser.add_argument('-c',       dest="Nthreads",         action="store",
                        help="Numbers of run_bash gnerate, i.e., numbers of cpu (threads) to use, default is 1",
                        type=int,   default=int(1) )

    args = parser.parse_args()
    indata_dir = './indata/'

    # Making Recipes -----------------------------------------------------------
    #target_have = make_recipe.check_obs_dates(args.targname, indata_dir)
    new_tar_list = os.listdir('./recipes/{}_recipes'.format(args.targname.replace(' ','')))
    target_have = np.sort([ int(dump[:8]) for dump in new_tar_list if dump[-1]=='p'])

    tenn = ''
    for iii in target_have:
        tenn = tenn + str(iii) + ' '
    print('-------------------------------------')
    print('process dates:\n', tenn)
    #target_have = np.array([20141123, 20151106, 20151108, 20151111])
    make_AB_recipe.move_data(args.targname, target_have)
