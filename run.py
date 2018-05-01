#!/usr/bin/env python

import sys, math
import os

def save_best_time(new_perf, best_so_far):
    for msg_size in new_perf:
        if msg_size not in best_so_far:
            best_so_far[msg_size] = new_perf[msg_size]
        else:
            best_so_far[msg_size] = min(best_so_far[msg_size], new_perf[msg_size])

#reads performance number from IMB results file
def read_performance_from_file(fname):
  perf = {}
  f = open(fname)

  #read until the performance lines
  for line in f:
    line = line.strip('\n\r ')
    if line.startswith('#bytes'):
      break
  
  #read performance numbers
  for line in f:
    line = line.strip('\r\n ')
    if line == '':
      break
    line = line.split(' ')
    line = [x for x in line if x]
    msg_size = int(line[0])
    perf[msg_size] = float(line[4])
  
  f.close()
  return perf

#append message size to file
def write_msgsize_to_file(fname, msgsize):
    f = open(fname, 'a')
    f.write(str(msgsize)+'\n')
    f.close()

np = int(sys.argv[1])
print "Number of ranks:", np
coll = sys.argv[2]
print "Collective to run:", coll
mode = sys.argv[3]
print "Script mode:", mode

imb_args = "-npmin " + str(np) + " -sync 1 -imb_barrier 1 -root_shift 0 -iter_policy multiple_np"
ibrun_args = "-n " + str(np) + " -ppn 1 -hostfile hostfile "
imb_exec = "../IMB-MPI1"
run_cmd = "mpirun " + ibrun_args + " " + imb_exec + " " + imb_args

bcast_time = {}
bcast_new_algos_best_time = {}
bcast_old_algos_best_time = {}
# Broadcast 
if coll == "Bcast":
    algo_ids = [1, 2, 3, 4, 5, 6, 7]
    k_vals = [i for i in range(2,15,2)]
    seg_sizes = [-1, 1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144, 524288]
    msg_logs = [i for i in range(0,22)]

    bcast_time["mpich_ofi"] = {}
    # MPICH-OFI new algorithm runs - algo 1 to 5
    for algo in [1,2,3,4,5]:
        print "Running new algo ", algo
        bcast_time["mpich_ofi"][algo] = {}
        env = "MPIR_CVAR_USE_BCAST="+str(algo)                                                          # set the algorithm id
        for seg_size in seg_sizes:                                                                      # iterate over all the segment sizes
            bcast_time["mpich_ofi"][algo][seg_size] = {}
            if algo == 1:                                                                               # ring algo
                env1 = env + " MPIR_CVAR_BCAST_RING_SEGSIZE=" + str(seg_size)
                open('msglenfile', 'w').close()                                                         #empty the msglenfile file
                for msg_log in msg_logs:
                    msg_size = int(math.pow(2, msg_log))
                    if msg_size > seg_size and msg_size/seg_size < 100:                                  # only run if message size is greater than segment size and there are not too many segments
                        write_msgsize_to_file("msglenfile", msg_size)

                dirname = "bcast/mpich_ofi/n_"+str(np)
                fname = "algo_"+str(algo)+".seg_"+str(seg_size)
                fpath = dirname + "/" + fname
                if mode == 'run':
                    os.system("mkdir -p " + dirname)
                    os.system(env1 + " " + run_cmd + " -msglen msglenfile " + coll + " > " + fpath)
                else: # mode is plot
                    bcast_time["mpich_ofi"][algo][seg_size] = read_performance_from_file(fpath)
                    save_best_time(bcast_time["mpich_ofi"][algo][seg_size], bcast_new_algos_best_time)

            else:                                                                                       # tree algos
                for k in k_vals:                                                                        # iterate over all the k values
                    bcast_time["mpich_ofi"][algo][seg_size][k] = {}
                    env1 = env + " MPIR_CVAR_BCAST_TREE_SEGSIZE=" + str(seg_size)
                    if (algo==1 or algo==3 or algo==4):                                                 # knomial trees
                        env2 = env1 + " MPIR_CVAR_BCAST_KNOMIAL_KVAL=" + str(k)
                    else:                                                                               # kary trees
                        env2 = env1 + " MPIR_CVAR_BCAST_KARY_KVAL=" + str(k)
                    open('msglenfile', 'w').close()                                                         #empty the msglenfile file
                    for msg_log in msg_logs:
                        msg_size = int(math.pow(2, msg_log))
                        if msg_size > seg_size and msg_size/seg_size < 100:                              # only run if message size is greater than segment size
                            write_msgsize_to_file("msglenfile", msg_size)

                    dirname = "bcast/mpich_ofi/n_"+str(np)
                    fname = "algo_"+str(algo)+".k_"+str(k)+".seg_"+str(seg_size)
                    fpath = dirname + "/" + fname
                    if mode == 'run':
                        os.system("mkdir -p " + dirname)
                        os.system(env2 + " " + run_cmd + " -msglen msglenfile " + coll + " > " + fpath)
                    else: # mode is plot
                        bcast_time["mpich_ofi"][algo][seg_size][k] = read_performance_from_file(fpath)
                        save_best_time(bcast_time["mpich_ofi"][algo][seg_size][k], bcast_new_algos_best_time)

    # MPICH-OFI Rabenseifner algorithm (algo=7)
    for algo in [6,8]:
        bcast_time["mpich_ofi"][algo] = {}
        print "Running Rabenseifner algo ", algo
        scatterv_kvals = [2, 3, 4, 5, 6]
        allgatherv_kvals = [2, 3, 4, 5]
        for scatterv_kval in scatterv_kvals:
            bcast_time["mpich_ofi"][algo][scatterv_kval] = {}
            for allgatherv_kval in allgatherv_kvals:
                bcast_time["mpich_ofi"][algo][allgatherv_kval] = {}
                dirname = "bcast/mpich_ofi/n_"+str(np)+"/"
                fname  = "algo_"+str(algo)+".scattervk_"+str(scatterv_kval)+".allgathervk_"+str(allgatherv_kval)
                fpath = dirname + "/" + fname
                if mode == 'run':
                    os.system("mkdir -p " + str(dirname))
                    os.system("MPIR_CVAR_USE_BCAST=" + str(algo) + " MPIR_CVAR_BCAST_HYBRID_SCATTERV_KVAL="+str(scatterv_kval) \
                            + " MPIR_CVAR_BCAST_HYBRID_ALLGATHERV_KVAL="+str(allgatherv_kval) + " " + run_cmd + " " + coll + " > " + fpath)
                else:
                    bcast_time["mpich_ofi"][algo][scatterv_kval][allgatherv_kval] = read_performance_from_file(fpath)
                    save_best_time(bcast_time["mpich_ofi"][algo][scatterv_kval][allgatherv_kval], bcast_new_algos_best_time)

    # MPICH old algorithm runs
    print "Running old algos"
    dirname = "bcast/mpich_ofi/n_"+str(np)+"/"
    fname = "algo_old_tree"
    fpath = dirname + "/" + fname
    if mode == 'run':
        os.system("mkdir -p " + dirname)
        os.system("MPIR_CVAR_BCAST_SHORT_MSG_SIZE=67108864 " + run_cmd  + " " + coll + " > " + fpath); 
    else:
        bcast_time["mpich_ofi"]["algo_old_tree"] = read_performance_from_file(fpath)
        save_best_time(bcast_time["mpich_ofi"]["algo_old_tree"], bcast_old_algos_best_time)

    dirname = "bcast/mpich_ofi/n_"+str(np)
    fname = "algo_old_medium"
    fpath = dirname + "/" + fname
    if mode == 'run':
        os.system("mkdir -p " + dirname)
        os.system("MPIR_CVAR_BCAST_SHORT_MSG_SIZE=0 MPIR_CVAR_BCAST_LONG_MSG_SIZE=67108864 " + run_cmd + " " + coll + " > " + fpath);
    else:
        bcast_time["mpich_ofi"]["algo_old_medium"] = read_performance_from_file(fpath)
        save_best_time(bcast_time["mpich_ofi"]["algo_old_medium"], bcast_old_algos_best_time)

    dirname = "bcast/mpich_ofi/n_"+str(np)
    fname = "algo_old_large"
    fpath = dirname + "/" + fname
    if mode == 'run':
        os.system("mkdir -p " + dirname)
        os.system("MPIR_CVAR_BCAST_SHORT_MSG_SIZE=0 MPIR_CVAR_BCAST_LONG_MSG_SIZE=0 " + run_cmd + " " + coll + " > " + fpath );
    else:
        bcast_time["mpich_ofi"]["algo_old_large"] = read_performance_from_file(fpath)
        save_best_time(bcast_time["mpich_ofi"]["algo_old_large"], bcast_old_algos_best_time)

    # Intel MPI run
    print "Running Intel MPI"
    dirname = "bcast/impi/n_"+str(np)
    fname = "default"
    fpath = dirname + "/" + fname
    if mode == 'run':
        os.system("mkdir -p " + dirname)
        os.system("LD_LIBRARY_PATH=/opt/intel/compilers_and_libraries_2017.4.196/linux/mpi/intel64/lib:$LD_LIBRARY_PATH " + run_cmd + " " + coll + " > " + fpath)
    else:
        bcast_time["impi"] = read_performance_from_file(fpath)

print bcast_new_algos_best_time
print bcast_old_algos_best_time
print bcast_time["impi"]
