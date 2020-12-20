from astropy.table import Table
import numpy as np
from os import listdir
from os.path import isfile, join
import glob
import sys, os
from pathlib import Path

# Readin the master log file
log_master = Table.read('./IGRINS_Full_Superlog_May2019.csv', format='csv')


def check_obs_dates(target_n, indata_dir, master=log_master):
    target = master[master['OBJNAME'] == target_n]
    u, indices = np.unique(target['CIVIL'], return_inverse=True)                # find unique obs date on target

    in_dates = [i for i in listdir( indata_dir ) if i[0]!='.']

    target_have = u[np.isin(u, in_dates)]
    #target_have = np.array(u[np.where( (u>=int(min(in_dates))) & (u<=int(max(in_dates))) )])

    print('-------------------------------------')
    print('{} days of observation on {} listed in master log. from {} to {}'.format(u.size, target_n, min(u), max(u)))
    print('{} days of observation on {} in indata dir also in master log. from {} to {}'.format(target_have.size, target_n, int(min(in_dates)), int(max(in_dates)) ))

    master = master[np.where( (master['CIVIL']>=int(min(in_dates))) & (master['CIVIL']<=int(max(in_dates))) )]
    master.sort(['CIVIL', 'FILENUMBER'])

    tenn = ''
    for iii in target_have:
        tenn = tenn + str(iii) + ' '
    print('-------------------------------------')
    print('process dates:\n', tenn)

    return target_have




def make_recipe(target_n, target_have, out_dir, master=log_master):

    no_flat = [] ; no_sky = [] ; no_std  = []
    target_Date = []
    target_ID   = []
    A0_ID       = []

    p = out_dir
    pp = Path(p)
    if pp.exists() == 0:
        os.mkdir( pp )


    for i in target_have:
        with open( p +'/' + str(i)+'.recipes.tmp', 'w') as f:
            #sys.stdout = f

            f.write('OBJNAME, OBJTYPE, GROUP1, GROUP2, EXPTIME, RECIPE, OBSIDS, FRAMETYPES\n')
            f.write('# Available recipes : FLAT, THAR, SKY, A0V_AB, A0V_ONOFF, STELLAR_AB, STELLAR_ONOFF, EXTENDED_AB, EXTENDED_ONOFF\n')

            # loop through all dates having your target
            date_file = master[master['CIVIL'] == i]

            # take our only your target, flat, STD, SKY star
            TAR  = date_file[date_file['OBJNAME'] == target_n]
            STD  = date_file[date_file['OBJTYPE'] == 'STD']
            SKY  = date_file[date_file['OBJNAME'] == 'SKY']

            # Use FLAT with FILENUMBER < 50 first, otherwise, use >50
            if sum([ (date_file['OBJTYPE'] == 'FLAT') & (date_file['FILENUMBER'] < 50)][0]) !=0:
                FLAT_t = date_file[ (date_file['OBJTYPE'] == 'FLAT') & (date_file['FILENUMBER'] < 50) ]
                if (sum([FLAT_t['FRAMETYPE']=='ON'][0]) != 0) & (sum([FLAT_t['FRAMETYPE']=='OFF'][0]) != 0):
                    FLAT = date_file[ (date_file['OBJTYPE'] == 'FLAT') & (date_file['FILENUMBER'] < 50) ]
                else: FLAT = 999

            elif sum([ (date_file['OBJTYPE'] == 'FLAT') & (date_file['FILENUMBER'] > 50)][0]) !=0:
                FLAT_t = date_file[ (date_file['OBJTYPE'] == 'FLAT') & (date_file['FILENUMBER'] > 50) ]
                if (sum([FLAT_t['FRAMETYPE']=='ON'][0]) != 0) & (sum([FLAT_t['FRAMETYPE']=='OFF'][0]) != 0):
                    FLAT = date_file[ (date_file['OBJTYPE'] == 'FLAT') & (date_file['FILENUMBER'] > 50) ]
                else: FLAT = 999

            if FLAT == 999:
                FLAT = date_file[ (date_file['OBJTYPE'] == 'FLAT')]

            # -----------------------------------------------------------------------------------------------------------
            # -----------------------------------------------------------------------------------------------------------
            # Flatten data in to form: OBJNAME, OBJTYPE, GROUP1, GROUP2, EXPTIME, RECIPE, OBSIDS, FRAMETYPES
            # For FLAT
            if len(FLAT) == 0:
                print('xxxxxxxxxxxxxx ', i, ' have not FLAT!!!')
                no_flat.append(i)
            else:
                OBJNAME = ['FLAT ON/OFF']; OBJTYPE = ['FLAT']; GROUP1 = []; GROUP2 = ['1']; EXPTIME = []; RECIPE = []; OBSIDS = ''; FRAMETYPES = '';
                temp = 0
                for j in FLAT:
                    if temp == 0:
                        GROUP1.append(j['FILENUMBER'])
                        EXPTIME.append(j['EXPTIME'])
                        RECIPE.append('FLAT')

                    OBSIDS = OBSIDS + str(j['FILENUMBER']) + ' '
                    FRAMETYPES = FRAMETYPES + str(j['FRAMETYPE']) + ' '
                    temp+=1
                #TAR_flatten = OBJNAME + OBJTYPE + GROUP1 + GROUP2 + EXPTIME + RECIPE + OBSIDS + FRAMETYPES
                aa = '{}, {}, {}, {}, {:.6f}, {},'.format(OBJNAME[0], OBJTYPE[0], GROUP1[0], GROUP2[0], int(EXPTIME[0]), RECIPE[0])
                f.write( aa + OBSIDS[:-1] + ', ' + FRAMETYPES[:-1] +'\n')

            # -----------------------------------------------------------------------------------------------------------
            # -----------------------------------------------------------------------------------------------------------
            # Flatten data in to form: OBJNAME, OBJTYPE, GROUP1, GROUP2, EXPTIME, RECIPE, OBSIDS, FRAMETYPES
            # For SKY
            if len(SKY) == 0:
                temp_exp = []
                for dump in date_file['EXPTIME']:
                    try:
                        temp_exp.append(int(dump))
                    except:
                        temp_exp.append(np.nan)
                # Use TAR with EXPTIME>=300s, and have most obs as SKY
                TAR_list150 = date_file[ (date_file['OBJTYPE'] == 'TAR') & ( np.array(temp_exp) >= 150) ]
                TAR_list300 = date_file[ (date_file['OBJTYPE'] == 'TAR') & ( np.array(temp_exp) >= 300) ]
                if len(TAR_list300) != 0:
                    TAR_list = TAR_list300
                else:
                    TAR_list = TAR_list150
                   # Get all TAR rows
                OBJ_U = np.unique(TAR_list['OBJNAME'])                  # Count number id targets

                num_obs = [np.char.count(TAR_list['OBJNAME'], runn).sum() for runn in OBJ_U] # Count number of observation for each targets

                try:
                    most_tar = OBJ_U[np.argmax(num_obs)]                    # Find the most obs target
                except:
                    print('No good sky for this date: ', i)
                    sys.exit()

                SKY  = date_file[date_file['OBJNAME'] == most_tar]

                # --------------------------------------------
                OBJNAME = [' ']; OBJTYPE = ['TAR']; GROUP1 = ['sky']; GROUP2 = ['1']; EXPTIME = []; RECIPE = ['SKY']; OBSIDS = ''; FRAMETYPES = '';
                temp = 0
                for j in SKY:
                    if temp == 0:
                        GROUP1 = str(j['FILENUMBER']) + GROUP1[0]
                        EXPTIME.append(j['EXPTIME'])
                    OBSIDS = OBSIDS + str(j['FILENUMBER']) + ' '
                    FRAMETYPES = FRAMETYPES + str(j['FRAMETYPE']) + ' '
                    temp+=1
                #TAR_flatten = OBJNAME + OBJTYPE + GROUP1 + GROUP2 + EXPTIME + RECIPE + OBSIDS + FRAMETYPES
                aa = '{}, {}, {}, {}, {:.6f}, {},'.format(OBJNAME[0], OBJTYPE[0], GROUP1, GROUP2[0], int(EXPTIME[0]), RECIPE[0])
                f.write( aa + OBSIDS[:-1] + ', ' + FRAMETYPES[:-1] +'\n')



                # --------------------------------------------
                if len(most_tar) == 0:
                    print('xxxxxxxxxxxxxx ', i, ' have no SKY!!!')
                    no_sky.append(i)
                # --------------------------------------------

            else:
                OBJNAME = [' ']; OBJTYPE = ['TAR']; GROUP1 = ['sky']; GROUP2 = ['1']; EXPTIME = []; RECIPE = ['SKY']; OBSIDS = ''; FRAMETYPES = '';
                temp = 0
                for j in SKY:
                    if temp == 0:
                        GROUP1 = str(j['FILENUMBER']) + GROUP1[0]
                        EXPTIME.append(j['EXPTIME'])
                        #RECIPE.append('FLAT')

                    OBSIDS = OBSIDS + str(j['FILENUMBER']) + ' '
                    FRAMETYPES = FRAMETYPES + str(j['FRAMETYPE']) + ' '
                    temp+=1
                #TAR_flatten = OBJNAME + OBJTYPE + GROUP1 + GROUP2 + EXPTIME + RECIPE + OBSIDS + FRAMETYPES
                aa = '{}, {}, {}, {}, {:.6f}, {},'.format(OBJNAME[0], OBJTYPE[0], GROUP1, GROUP2[0], int(EXPTIME[0]), RECIPE[0])
                f.write( aa + OBSIDS[:-1] + ', ' + FRAMETYPES[:-1] +'\n')

            # -----------------------------------------------------------------------------------------------------------
            # -----------------------------------------------------------------------------------------------------------
            # For STD
            # Find Best STD to use
            if len(STD) == 0:
                print('xxxxxxxxxxxxxx ', i, ' have no STD!!!')
                no_std.append(i)
                A0_ID.append(999)
            else:
                #------------------------------------------------------------------------------
                STD['AM']= STD['AM'].astype(float)
                STD['FILENUMBER']= STD['FILENUMBER'].astype(float)

                ## Find how many sets of STDs
                dump = 0 ; dump1 = 0
                for c in range(len(STD)-1):
                    if (STD['FILENUMBER'][c+1] - STD['FILENUMBER'][c] == 1) & ( float(STD['EXPTIME'][c+1]) - float(STD['EXPTIME'][c]) == 0) & (dump == 0):
                        STD['GROUP1'][c] = STD['FILENUMBER'][c]
                        #STD['GROUP2'][c] = dump1
                        dump+=1
                    elif (STD['FILENUMBER'][c+1] - STD['FILENUMBER'][c] == 1) & ( float(STD['EXPTIME'][c+1]) - float(STD['EXPTIME'][c]) == 0) & (dump != 0):
                        STD['GROUP1'][c] = STD['FILENUMBER'][c-dump]
                        #STD['GROUP2'][c] = dump1
                        dump+=1
                    else:
                        STD['GROUP1'][c] = STD['FILENUMBER'][c-dump]
                        #STD['GROUP2'][c] = dump1
                        dump=0
                        #dump1+=1
                STD['GROUP1'][len(STD)-1] = STD['FILENUMBER'][len(STD)-1-dump]
                #STD['GROUP2'][len(STD)-1] = dump1

                # ---------
                STD_set_n = np.unique(STD['GROUP1'])
                STD_set_n = STD_set_n.astype(float)
                STD_AM_mean = [ np.mean(STD['AM'][STD['FILENUMBER']==ii] ) for ii in STD_set_n]
                STD_FILE_mean = [ np.mean(STD['FILENUMBER'][STD['FILENUMBER']==ii] ) for ii in STD_set_n]

                # Find the nearest two sets of STD
                TAR['FILENUMBER'] = TAR['FILENUMBER'].astype(float)
                TAR_FILE_mean = np.mean(TAR['FILENUMBER'])

                differ_FILE = abs(STD_FILE_mean - TAR_FILE_mean)

                temp1 = Table(data=(STD_set_n, differ_FILE),
                              names=('file_n', 'differ'))
                temp1.sort('differ')

                temp1['file_n'] = temp1['file_n'].astype(int)

                # Find the most similar AirMass between the two STD sets with TAR

                TAR['AM'] = TAR['AM'].astype(float)
                TAR_AM_mean = np.mean(TAR['AM'])

                t_group1 = np.array(STD['GROUP1'], dtype=float)

                if len(temp1) == 1:
                    use_STD_loc = np.where( t_group1 == temp1['file_n'][0])[0]
                else:
                    loc_1set = np.where( t_group1 == temp1['file_n'][0])[0]
                    loc_2set = np.where( t_group1 == temp1['file_n'][1])[0]

                    differ1 = abs( np.mean(STD['AM'][loc_1set]) - TAR_AM_mean)
                    differ2 = abs( np.mean(STD['AM'][loc_2set]) - TAR_AM_mean)   # Caculate the differnce

                    use_STD_loc = []
                    if differ1 < differ2:
                        use_STD_loc = loc_1set
                    elif  differ1 > differ2:
                        use_STD_loc = loc_2set
                    else:
                        use_STD_loc = loc_1set

                #------------------------------------------------------------------------------

                OBJNAME = [STD[use_STD_loc[0]]['OBJNAME']]; OBJTYPE = ['STD']; GROUP1 = []; GROUP2 = ['1']; EXPTIME = []; RECIPE = []; OBSIDS = ''; FRAMETYPES = '';
                GROUP1_STD = []
                temp = 0
                for j in STD[use_STD_loc]:
                    if temp == 0:
                        GROUP1.append(j['FILENUMBER'])
                        GROUP1_STD.append(j['FILENUMBER'])
                        EXPTIME.append(j['EXPTIME'])
                        RECIPE.append('A0V_AB')

                        A0_ID.append(int(j['FILENUMBER']))

                    OBSIDS = OBSIDS+ ' ' + str(j['FILENUMBER'])[:-2]
                    #OBSIDS = int(OBSIDS)
                    FRAMETYPES = FRAMETYPES + str(j['FRAMETYPE']) + ' '
                    FRAMETYPES_STD = FRAMETYPES
                    temp+=1
                #TAR_flatten = OBJNAME + OBJTYPE + GROUP1 + GROUP2 + EXPTIME + RECIPE + OBSIDS + FRAMETYPES
                aa = '{}, {}, {}, {}, {:.6f}, {},'.format(OBJNAME[0], OBJTYPE[0], int(GROUP1[0]), GROUP2[0], int(EXPTIME[0]), RECIPE[0])
                f.write(aa + OBSIDS + ', ' + FRAMETYPES[:-1] +'\n')
                #print('-----')

            # -----------------------------------------------------------------------------------------------------------
            # -----------------------------------------------------------------------------------------------------------
            # For TAR
            # For Choosing STD for TAR, let GROUP2 number be the STD FILENUMBER
            OBJNAME = [target_n]; OBJTYPE = ['TAR']; GROUP1 = []; GROUP2 = [int(GROUP1_STD[0])]; EXPTIME = []; RECIPE = []; OBSIDS = ''; FRAMETYPES = '';
            temp = 0
            for j in TAR:
                if temp == 0:
                    GROUP1.append(j['FILENUMBER'])
                    EXPTIME.append(j['EXPTIME'])
                    RECIPE.append('STELLAR_AB')

                    target_Date.append(i)
                    target_ID.append(int(j['FILENUMBER']))

                OBSIDS = OBSIDS + str(int(j['FILENUMBER'])) + ' '
                FRAMETYPES = FRAMETYPES + str(j['FRAMETYPE']) + ' '
                FRAMETYPES_TAR = FRAMETYPES
                temp+=1



            #TAR_flatten = OBJNAME + OBJTYPE + GROUP1 + GROUP2 + EXPTIME + RECIPE + OBSIDS + FRAMETYPES
            aa = '{}, {}, {}, {}, {:.6f}, {},'.format(OBJNAME[0], OBJTYPE[0], int(GROUP1[0]), GROUP2[0], int(EXPTIME[0]), RECIPE[0])
            f.write( aa + OBSIDS[:-1] + ', ' + FRAMETYPES[:-1] +'\n')


            #sys.stdout = sys.__stdout__

            if len([ i for i in FRAMETYPES_STD.split(' ') if i != ''] )%2 != 0:
                print('-------------------------------------')
                print('---!!!!!!!!!!-Worning-!!!!!!!!!!!----')
                print(i, ' is showing odd AB pair in STD: ', FRAMETYPES_STD, 'please go into the recipe.tmp and make it even')

            if len([ i for i in FRAMETYPES_TAR.split(' ') if i != ''] )%2 != 0:
                print('-------------------------------------')
                print('---!!!!!!!!!!-Worning-!!!!!!!!!!!----')
                print(i, ' is showing odd AB pair in TAR: ', FRAMETYPES_TAR, 'please go into the recipe.tmp and make it even')

        f = open(p + '/' + 'worning_recipes.txt', 'w')
        f.write('no flat: '+ str(no_flat)+ '\n' )
        f.write('no sky: '+ str(no_sky)+ '\n' )
        f.write('no std: '+ str(no_std) )
        f.close()

        TAR_ID = Table(data=(target_Date, target_ID, A0_ID), names=('Date', 'ID', 'A0ID'))
        TAR_ID.write(p + '/' + target_n.replace(' ','') + '_TAR_ID.csv', format='csv', overwrite=True)
