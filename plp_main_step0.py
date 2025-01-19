import os, sys, argparse
from astroquery.simbad import Simbad
import numpy as np
import pandas as pd



def RRISA_v3_search(tar):
    customSimbad = Simbad()
    # customSimbad.add_votable_fields('pmra', 'pmdec')
    try:    
        res_tab = customSimbad.query_object(tar)
    except:
        sys.exit('Simbad query failed, please check your target name.')
    
    main_id = res_tab['MAIN_ID'][0]
    print('-------------------------------------')
    print('Simbad MAIN_ID: ', main_id)

    # read xmatch_log.csv with pandas
    xmatch_log = pd.read_csv('./xmatch_log.csv')

    # get the row of the target
    tar_df = xmatch_log[xmatch_log['NAME'] == main_id]
    # print(f'We got {len(tar_df)} rows for {main_id} in xmatch_log.csv')

    civil = tar_df['CIVIL'].to_numpy()
    print(f'{main_id} have {len(tar_df)} observations: {civil}.')

    return civil




if __name__ == "__main__":
    print('\nStep 0...')

    parser = argparse.ArgumentParser(
                                     prog        = 'igrins plp v3.0 modified for IGRINS RV, IGRINS Radial Velocity Pipeline',
                                     description = '''
                                     plp_main_step0.py help user to get the unique nights of observations for the target list.
                                     IGRINS is currently stored on UT Austin's BOX, which don't allow scripting to download folders
                                     of data. User can use this .py to search for the unique nights of observations that have the target.
                                     ''',
                                     epilog = "Contact authors: asa.stahl@rice.edu; sytang@lowell.edu")
    parser.add_argument("targname",                          action="store",
                        help="Enter your *target names, should be simbad searchable or simbad MAIN ID. Example >> \"CI Tau, DI Tau\"", type=str)

    args = parser.parse_args()
    target_list = args.targname.split(', ')
    print('\n-------------------------------------')
    print(f'Your target list: {target_list}')

    # check if "xmatch_log.csv" exists
    print(f'\nSearching target in the ./xmatch_log.csv from RRISA...')
    if not os.path.exists('./xmatch_log.csv'):
        sys.exit('    ERROR! xmatch_log.csv not found, please get it from RRISA, first.')


    night_box = np.array([])
    for targ in target_list:
        # Get the Date of observations for your target so you can manually download the raw data
        civil = RRISA_v3_search(targ)

        night_box = np.append(night_box, np.unique(civil))
    
    
    print('\n-------------------------------------')
    print(f'Unique nights to download for target {target_list}: {night_box}')

    print('Step 0 DONE!')


