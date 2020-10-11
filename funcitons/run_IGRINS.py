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
        fh.write('  for RECIPE in flat register-sky sky-wvlsol\n')
        fh.write('  do\n')
        fh.write('      python igr_pipe.py $RECIPE $UTDATE \n')
        fh.write('      rc=$?\n')
        fh.write('      if [ $rc != "0" ]\n')
        fh.write('      then\n')
        fh.write('          exit $rc\n')
        fh.write('      fi\n')
        fh.write('  done\n')
        fh.write('\n')
        fh.write('  python igr_pipe.py a0v-ab $UTDATE --basename-postfix="_A" --frac-slit="0,0.5"\n')
        fh.write('  python igr_pipe.py a0v-ab $UTDATE --basename-postfix="_B" --frac-slit="0.5,1"\n')
        fh.write('  python igr_pipe.py stellar-ab $UTDATE --basename-postfix="_A" --frac-slit="0,0.5"\n')
        fh.write('  python igr_pipe.py stellar-ab $UTDATE --basename-postfix="_B" --frac-slit="0.5,1"\n')
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