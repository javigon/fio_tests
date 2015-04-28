import os
import time
import subprocess

device = 'nvme0n1'

fio_size="1G" # size in fio
fio_runtime="5" # runtime in fio for time_based tests

# fio --minimal hardcoded positions
fio_iops_pos=7
fio_slat_pos_start=9
fio_clat_pos_start=13
fio_lat_pos_start=37

kernel_version = os.uname()[2]
columns="iotype;bs;njobs;iodepth;iops;slatmin;slatmax;slatavg;clatmin;clatmax;clatavg;latmin;latmax;latavg"

# Eliminate noise by running each test n times and calculating average.
n_iterations=3

f = open(kernel_version + time.strftime("%H%M%S") + "-fio.csv", "w+")
f.write(columns+"\n")

for run in ('write', 'randwrite', 'read', 'randread'):
    for blocksize in ('512', '1k', '4k', '512k'):
        for numjobs in (1, 32, 64):
            for iodepth in (1, 8, 32, 64, 128):
                fio_type_offset = 0
                iops = 0.0
                slat = [0.0 for i in range(3)]
                clat = [0.0 for i in range(3)]
                lat = [0.0 for i in range(3)]

                result = "" + str(run) + ";" + str(blocksize) + ";" + str(numjobs) + ";" + str(iodepth) + ";"
                command = "sudo fio --minimal -name=temp-fio --bs="+str(blocksize)+" --ioengine=libaio --iodepth="+str(iodepth)+" --size="+fio_size+" --direct=1 --rw="+str(run)+" --filename=/dev/"+str(device)+" --numjobs="+str(numjobs)+" --time_based --runtime="+fio_runtime+" --group_reporting"
                print (command)

                for i in range (0, n_iterations):
                    os.system("sleep 2") #Give time to finish inflight IOs
                    output = subprocess.check_output(command, shell=True)
                    if "write" in run:
                        fio_type_offset=41

                    # fio is called with --group_reporting. This means that all
                    # statistics are group for different jobs.

                    # iops
                    iops = iops + float(output.split(";")[fio_type_offset + fio_iops_pos])

                    # slat
                    for j in range (0, 3):
                        slat[j] = slat[j] + float(output.split(";")[fio_type_offset+fio_slat_pos_start+j])
                    # clat
                    for j in range (0, 3):
                        clat[j] = clat[j] + float(output.split(";")[fio_type_offset+fio_clat_pos_start+j])
                    # lat
                    for j in range (0, 3):
                        lat[j] = lat[j] + float(output.split(";")[fio_type_offset+fio_lat_pos_start+j])

                # iops
                result = result+str(iops / n_iterations)
                # slat
                for i in range (0, 3):
                    result = result+";"+str(slat[i] / n_iterations)
                # clat
                for i in range (0, 3):
                    result = result+";"+str(clat[i] / n_iterations)
                # lat
                for i in range (0, 3):
                    result = result+";"+str(lat[i] / n_iterations)

                print (result)
                f.write(result+"\n")
                f.flush()

f.closed

