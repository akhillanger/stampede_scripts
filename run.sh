#!/usr/bin/bash

pwd
np=$1
echo "Number of ranks: "$np
coll=$2
echo "Collective to run: "$coll

imb_args="-npmin $np -sync 1 -imb_barrier 1 -root_shift 0 -iter_policy multiple_np Bcast"
ibrun_args="-n $np"
imb_exec=../IMB-MPI1
run_cmd="ibrun $ibrun_args $imb_exec $imb_args"

# Broadcast 
if [ $coll == Bcast ]; then
    algo_ids=(1 2 3 4 5 6 7)
    k_vals=($(seq 2 1 20))
    seg_sizes=(-1 1024 2048 4096 8192 16384 32768 65536 131072 262144 524288)
    msg_logs=($(seq 0 1 22))

    # MPICH-OFI new algorithm runs
    for algo in ``
    do
        env=MPIR_CVAR_USE_BCAST=$algo                                                   # set the algorithm id
        for seg_size in ${seg_sizes[@]}                                                 # iterate over all the segment sizes
        do
            if [ $algo -eq 5 ]                                                          # ring algo
            then
                env1="$env MPIR_CVAR_BCAST_RING_SEGSIZE=$seg_size"
                for msg_log in ${msg_logs[@]}
                do
                    msg_size=$((2**$msg_log))
                    if [ $msg_size -gt $seg_size ]                                      # only run if message size is greater than segment size
                    then
                        fname=bcast/mpich_ofi/n_${np}/msgsz_${msg_size}/algo_${algo}.seg_$seg_size
                        mkdir -p "${fname%/*}"
                        eval "$env1 $run_cmd -msglog $msg_log:$msg_log > ${fname}"
                    fi
                done
            else                                                                        # tree algos
                for k in ${k_vals[@]}                                                   # iterate over all the k values
                do
                    env1="$env MPIR_CVAR_BCAST_TREE_SEGSIZE=$seg_size"
                    if [ $algo -eq 1 ] || [ $algo -eq 3 ] || [ $algo -eq 4 ]            # knomial trees
                    then
                        env2="$env1 MPIR_CVAR_BCAST_KNOMIAL_KVAL=${k}"
                    else                                                                # kary trees
                        env2="$env1 MPIR_CVAR_BCAST_KARY_KVAL=${k}"
                    fi
                    for msg_log in ${msg_logs[@]}
                    do
                        msg_size=$((2**$msg_log))
                        if [ $msg_size -gt $seg_size ]                                  #only run if message size is greater than segment size
                        then
                            fname=bcast/mpich_ofi/n_${np}/msgsz_${msg_size}/algo_${algo}.k_${k}.seg_$seg_size
                            mkdir -p "${fname%/*}"
                            eval "$env2 $run_cmd -msglog $msg_log:$msg_log > ${fname}"
                        fi
                    done
                done
            fi
        done
    done

    # MPICH-OFI Rabenseifner algorithm (algo=7)
    scatterv_kvals=(2 3 4 5 6 7 8)
    allgatherv_rec_exch_kvals=(2 3 4 5 6)
    for scatterv_kval in ${scatterv_kvals[@]}
    do
        for allgatherv_rec_exch_kval in ${allgatherv_rec_exch_kvals[@]}
        do
            fname=bcast/mpich_ofi/n_${np}/algo_${algo}.scattervk_${scatterv_kval}.allgathervk_${allgatherv_rec_exch_kval}
            mkdir -p "${fname%/*}"
            eval "MPIR_CVAR_USE_BCAST=7 MPIR_CVAR_BCAST_HYBRID_SCATTERV_KVAL=${scatterv_kval} \
                MPIR_CVAR_BCAST_HYBRID_ALLGATHERV_KVAL=${allgatherv_rec_exch_kval} $run_cmd > ${fname}"
        done
    done

    # MPICH old algorithm runs
    MPIR_CVAR_BCAST_SHORT_MSG_SIZE=67108864 $run_cmd > bcast/bcast.mpich_ofi.n_${np}.algo_old_tree
    MPIR_CVAR_BCAST_SHORT_MSG_SIZE=0 MPIR_CVAR_BCAST_LONG_MSG_SIZE=67108864 $run_cmd > bcast/bcast.mpich_ofi.n_${np}.algo_old_medium
    MPIR_CVAR_BCAST_SHORT_MSG_SIZE=0 MPIR_CVAR_BCAST_LONG_MSG_SIZE=0 $run_cmd > bcast/bcast.mpich_ofi.n_${np}.algo_old_large

    # Intel MPI run
    LD_LIBRARY_PATH=/opt/intel/compilers_and_libraries_2017.4.196/linux/mpi/intel64/lib:$LD_LIBRARY_PATH $run_cmd > bcast/bcast.impi.n_${np}
fi
