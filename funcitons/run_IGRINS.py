import numpy as np
import os
import pandas as pd
import re

def making(target_n, utdates, tim):
    with open('./run_sh/{:s}_run_igrins{}.sh'.format(target_n.replace(' ',''), tim), 'w') as fh:
        fh.write("#!/usr/bin/env bash\n")
        fh.write("cd ../\n")
        fh.write("source activate igr-pipe\n")

        fh.write("for UTDATE in")
        for ut in utdates:
            fh.write(" {}".format(ut) )
        fh.write('\n')

        fh.write('do\n')
        fh.write('  echo Processing $UTDATE\n')
        #fh.write('  for RECIPE in flat register-sky sky-wvlsol a0v-ab a0v-onoff stellar-ab extended-ab extended-onoff stellar-onoff tell-wvsol\n')
        fh.write('  for RECIPE in flat register-sky sky-wvlsol a0v-ab a0v-onoff stellar-ab\n')
        fh.write('  do\n')
        fh.write('      python igr_pipe.py $RECIPE $UTDATE\n')
        fh.write('      rc=$?\n')
        fh.write('      if [ $rc != "0" ]\n')
        fh.write('      then\n')
        fh.write('          exit $rc\n')
        fh.write('      fi\n')
        fh.write('  done\n')
        fh.write('\n')
        fh.write('  if [ $rc != "0" ]\n')
        fh.write('  then\n')
        fh.write('      exit $rc\n')
        fh.write('  fi\n')
        fh.write('done\n')
        fh.write('\n')
        fh.write("echo IGRINS Pipeline Finished\n")

        fh.write("conda deactivate\n")

#pwd = os.getcwd()
def make_sh(target_n, target_have, cpu_use):
    print('-------------------------------------')
    print('Making .sh file')
    utdates = np.sort(target_have)

    delta = len(target_have) // cpu_use
    remain= cpu_use % delta
    for i in range(cpu_use):
        if i != cpu_use-1:
            making(target_n, utdates[i*delta:(i+1)*delta], i+1)
        elif i == cpu_use-1:
            making(target_n, utdates[i*delta:], i+1)





def move_data(target_n, target_have):
    recipe_files = glob.glob('./recipe_files_{0:s}/*.recipes'.format(star.replace(' ', '')))

    utdates = target_have
    in_spec_fh = '/Volumes/data/IGRINS/outdata/{0:d}/SDC{1:s}_{0:d}_{2:04d}.spec.fits'
    in_sn_fh = '/Volumes/data/IGRINS/outdata/{0:d}/SDC{1:s}_{0:d}_{2:04d}.sn.fits'
    out_spec_fh = './{0:s}/{1:d}/{2:s}/SDC{3:s}_{1:d}_{4:04d}.spec.fits'
    out_sn_fh = './{0:s}/{1:d}/{2:s}/SDC{3:s}_{1:d}_{4:04d}.sn.fits'

    new_recipe_fh_new   = pwd + '/IGRINS/plp-master/recipe_logs/' + '{0:8d}.recipes'



    for jj, ut in enumerate(utdates):
        print("{0:d}".format(ut))
        recipe  = pd.read_csv(new_recipe_fh_new.format(utdate), comment='#')
        science = recipe[recipe['OBJNAME'].str.contains(target_n, regex=True, flags=re.IGNORECASE)]


        recipe = pd.read_csv(recipe_files[jj], comment='#')
        science  = recipe[recipe['OBJNAME'].str.contains(star)]
        science = science.reset_index()
        std = recipe[recipe[' OBJTYPE'].str.contains('STD')]
        mkdir("{0:s}/{1:d}/AB/".format(star.replace(' ', ''), ut))
        mkdir("std/{0:d}/AB/".format(ut))
        mkdir("{0:s}/{1:d}/A/".format(star.replace(' ', ''), ut))
        mkdir("{0:s}/{1:d}/B/".format(star.replace(' ', ''), ut))
        for kk, x in science.iterrows():
            _frames = x[' FRAMETYPES'].strip().split(' ')
            _ids = [int(y) for y in x[' OBSIDS'].strip().split(' ')]
            for b in ['H', 'K']:
                if _ids[0] < 1000:
                    try:
                        copyfile(in_spec_fh.format(ut, b, _ids[0]), out_spec_fh.format(star.replace(' ',''), ut, 'AB', b, _ids[0]))
                        copyfile(in_sn_fh.format(ut, b, _ids[0]), out_sn_fh.format(star.replace(' ',''), ut, 'AB', b, _ids[0]))
                    except:
                        print("Failed to copy: " +  in_spec_fh.format(ut, b, _ids[0]))
                        pass
                else:
                    try:
                        copyfile(in_spec_fh.format(ut, b, _ids[0]), out_spec_fh.format(star.replace(' ',''), ut, _frames[0], b, _ids[0]-1000))
                        copyfile(in_sn_fh.format(ut, b, _ids[0]), out_sn_fh.format(star.replace(' ',''), ut, _frames[0], b, _ids[0]-1000))
                    except:
                        print("Failed to copy: " + in_spec_fh.format(ut, b, _ids[0]))
                        pass
        for kk, x in std.iterrows():
            _frames = x[' FRAMETYPES'].strip().split(' ')
            _ids = [int(y) for y in x[' OBSIDS'].strip().split(' ')]
            for b in ['H', 'K']:
                try:
                    copyfile(in_spec_fh.format(ut, b, _ids[0]), out_spec_fh.format('std', ut, 'AB', b, _ids[0]))
                    copyfile(in_sn_fh.format(ut, b, _ids[0]), out_sn_fh.format('std', ut, 'AB', b, _ids[0]))
                except:
                    print("Failed to copy: " +  in_spec_fh.format(ut, b, _ids[0]))
                    pass
