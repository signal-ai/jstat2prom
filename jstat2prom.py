"""
jstat2prom
"""

import subprocess
import time
import re
import shutil

INTERVAL = '15s'
COUNT = "10000"
SLEEP_TIME = 15
PROM_DIR = "/tmp"
METRIC_PREFIX = "jstat"

# List of metrics:
# jvm_mem_heap_used_bytes gauge
# jvm_mem_heap_max_bytes gauge
# jvm_mem_non_heap_used_bytes gauge
# jvm_mem_non_heap_max_bytes gauge
# jvm_mem_pools_young_used_bytes gauge
# jvm_mem_pools_young_max_bytes gauge
# jvm_mem_pools_old_used_bytes gauge
# jvm_mem_pools_old_max_bytes gauge
# jvm_gc_collectors_young_collection_count counter
# jvm_gc_collectors_young_collection_time_seconds gauge
# jvm_gc_collectors_old_collection_count counter
# jvm_gc_collectors_old_collection_time_seconds gauge


def get_pid():
    try:
        return subprocess.check_output(
            ['pgrep', 'java'],
            stderr=subprocess.STDOUT).decode('ascii').rstrip()
    except subprocess.CalledProcessError:
        return None


def write_to_prom(metrics):
    data = ""
    for k, v in metrics.iteritems():
        if METRIC_PREFIX:
            k = METRIC_PREFIX + "_" + k
            data += "# HELP " + k + "\n"
        if "_count" in k:
            data += "# TYPE " + k + " counter\n"
        else:
            data += "# TYPE " + k + " gauge\n"
        data += k + " " + str(v) + "\n"
    print data
    file = open(PROM_DIR + '/jstat.tmp', 'w')
    file.write(data)
    file.close()
    shutil.move(PROM_DIR + '/jstat.tmp', PROM_DIR + '/jstat.prom')
    return


def get_metrics(data):
    # https://stackoverflow.com/questions/1262328/how-is-the-java-memory-pool-divided
    # heap = survivor + eden + old
    # non heap = metaspace + codecache (cc)
    # young pool = survivor + eden
    # old pool = tenured
    metrics = {
        'jvm_mem_heap_max_bytes': float(data[0]) + float(data[1])
        + float(data[4]) + float(data[6]),
        'jvm_mem_heap_used_bytes': float(data[2]) + float(data[3])
        + float(data[5]) + float(data[7]),
        'jvm_mem_non_heap_max_bytes': float(data[8]) + float(data[10]),
        'jvm_mem_non_heap_used_bytes': float(data[9]) + float(data[11]),
        'jvm_mem_pools_young_max_bytes': float(data[0]) + float(data[1])
        + float(data[4]),
        'jvm_mem_pools_young_used_bytes': float(data[2]) + float(data[3])
        + float(data[5]),
        'jvm_mem_pools_old_max_bytes': float(data[6]),
        'jvm_mem_pools_old_used_bytes': float(data[7]),
        'jvm_gc_collectors_young_collection_count': data[12],
        'jvm_gc_collectors_young_collection_time_seconds': data[13],
        'jvm_gc_collectors_old_collection_count': data[14],
        'jvm_gc_collectors_old_collection_time_seconds': data[15]
    }

    # Convert kbytes into bytes
    for k, v in metrics.iteritems():
        if "bytes" in k:
            metrics[k] = v * 1024
    return metrics


def read_from_jstat():
    command = ['jstat', '-gc']
    pid = get_pid()
    command.append(pid)
    command.append(INTERVAL)
    command.append(COUNT)
    if pid:
        print "Running jstat against jvm pid {}. Interval: {}".format(
            pid, INTERVAL)
        try:
            p = subprocess.Popen(
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            while True:
                line = p.stdout.readline()
                data = re.findall(r'\d+\.?\d*', line)
                print data
                if (len(data)) == 16:    # jstat will not show FGC value when
                    data.insert(14, "0")  # there is no old GCs
                if (len(data)) == 17:
                    metrics = get_metrics(data)
                    write_to_prom(metrics)
                retcode = p.poll()
                if retcode is not None:
                    print "jstat died. Exiting."
                    time.sleep(SLEEP_TIME)
                    break
        except EnvironmentError as e:
            print "Something bad happened: " + str(e)
            time.sleep(SLEEP_TIME)
            return
    else:
        print "Can't get jvm pid. Sleeping for {} seconds.".format(
            str(SLEEP_TIME))
        time.sleep(SLEEP_TIME)


if __name__ == '__main__':
    while True:
        read_from_jstat()
