#!/usr/bin/env python

import sys, math
import os

def read_imb_results_file(f, results):
    for line in f:


np = int(sys.argv[1])
print "Number of ranks:", np
coll = sys.argv[2]
print "Collective to run:", coll

imb_args = "-npmin " + str(np) + " -sync 1 -imb_barrier 1 -root_shift 0 -iter_policy multiple_np Bcast"
ibrun_args = "-n " + str(np)
imb_exec = "../IMB-MPI1"
run_cmd = "ibrun " + ibrun_args + " " + imb_exec + " " + imb_args

bcast_time = {}
# Broadcast 
if coll == "Bcast":
    algo_ids = [1, 2, 3, 4, 5, 6, 7]
    k_vals = [i for i in range(2,15,2)]
    seg_sizes = [-1, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288]
    msg_logs = [i for i in range(0,22)]

    bcast_time["mpich_ofi"] = {}
    # MPICH-OFI new algorithm runs - algo 1 to 5
    for algo in [1, 2, 3, 4, 5]:
        bcast_time["mpich_ofi"][algo] = {}
        env = "MPIR_CVAR_USE_BCAST="+str(algo)                                                          # set the algorithm id
        for seg_size in seg_sizes:                                                                      # iterate over all the segment sizes
            if algo == 5:                                                                               # ring algo
                env1 = env + " MPIR_CVAR_BCAST_RING_SEGSIZE=" + str(seg_size)
                for msg_log in msg_logs:
                    msg_size = math.pow(2, msg_log)
                    if msg_size > seg_size && msg_size/seg_size < 100:                                  # only run if message size is greater than segment size and there are not too many segments
                        dirname = "bcast/mpich_ofi/n_"+str(np)+"/msgsz_"+str(msg_size)
                        fname = "algo_"+str(algo)+".seg_"+str(seg_size)
                        os.system("mkdir -p " + dirname)
                        os.system(env1 + " " + run_cmd + " -msglog " + str(msg_log)+":"+str(msg_log) + " > " + dirname + "/" + fname)

                        bcast_time["mpich_ofi"][algo][seg_size] = {}
                        bcast_time["mpich_ofi"][algo][seg_size][msg_size] = {}

            else:                                                                                       # tree algos
                for k in k_vals:                                                                        # iterate over all the k values
                    env1 = env + " MPIR_CVAR_BCAST_TREE_SEGSIZE=" + str(seg_size)
                    if (algo==1 or algo==3 or algo==4):                                                 # knomial trees
                        env2 = env1 + " MPIR_CVAR_BCAST_KNOMIAL_KVAL=" + str(k)
                    else:                                                                               # kary trees
                        env2 = env1 + " MPIR_CVAR_BCAST_KARY_KVAL=" + str(k)
                    for msg_log in msg_logs:
                        msg_size = math.pow(2, msg_log)
                        if msg_size > seg_size && msg_size/seg_size < 100:                              # only run if message size is greater than segment size
                            dirname = "bcast/mpich_ofi/n_"+str(np)+"/msgsz_"+str(msg_size)+"/"
                            fname = "algo_"+str(algo)+".k_"+str(k)+".seg_"+str(seg_size)
                            os.system("mkdir -p " + dirname)
                            os.system(env2 + " " + run_cmd + " -msglog " + str(msg_log)+":"+str(msg_log) + " > " + dirname + "/" + fname)

    # MPICH-OFI Rabenseifner algorithm (algo=7)
    scatterv_kvals = [2, 3, 4, 5, 6, 7, 8]
    allgatherv_kvals = [2, 3, 4, 5]
    for scatterv_kval in scatterv_kvals:
        for allgatherv_kval in allgatherv_kvals:
            dirname = "bcast/mpich_ofi/n_"+str(np)+"/"
            fname  = "algo_"+str(algo)+".scattervk_"+str(scatterv_kval)+".allgathervk_"+str(allgatherv_kval)
            os.system("mkdir -p " + str(dirname))
            os.system("MPIR_CVAR_USE_BCAST=7 MPIR_CVAR_BCAST_HYBRID_SCATTERV_KVAL="+str(scatterv_kval) \
                    + "MPIR_CVAR_BCAST_HYBRID_ALLGATHERV_KVAL="+str(allgatherv_kval) + " " + run_cmd + " > " + dirname + "/" + fname)

    # MPICH old algorithm runs
    dirname = "bcast/mpich_ofi/n_"+str(np)+"/"
    fname = "algo_old_tree"
    os.system("mkdir -p " + dirname)
    os.system("MPIR_CVAR_BCAST_SHORT_MSG_SIZE=67108864 " + run_cmd  + " > " + dirname + "/" + fname); 

    dirname = "bcast/mpich_ofi/n_"+str(np)
    fname = "algo_old_medium"
    os.system("mkdir -p " + dirname)
    os.system("MPIR_CVAR_BCAST_SHORT_MSG_SIZE=0 MPIR_CVAR_BCAST_LONG_MSG_SIZE=67108864 " + run_cmd + " > " + dirname + "/" + fname);

    dirname = "bcast/mpich_ofi/n_"+str(np)
    fname = "algo_old_large"
    os.system("mkdir -p " + dirname)
    os.system("MPIR_CVAR_BCAST_SHORT_MSG_SIZE=0 MPIR_CVAR_BCAST_LONG_MSG_SIZE=0 " + str(run_cmd) + " > " + dirname + "/" + fname );

    # Intel MPI run
    dirname = "bcast/impi/n_"+str(np)
    fname = "default"
    os.system("mkdir -p " + dirname)
    os.system("LD_LIBRARY_PATH=/opt/intel/compilers_and_libraries_2017.4.196/linux/mpi/intel64/lib:$LD_LIBRARY_PATH " + run_cmd + " > " + dirname + "/" + fname)
fi
