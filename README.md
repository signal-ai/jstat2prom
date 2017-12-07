# About
jstat2prom collects JVM garbage collection and memory stats through jstat and converts 
them into Textfile Collector format that can be pulled by Prometheus using the node 
exporter with `--collector.textfile.directory /path/to/directory`.

## Requirements
jstat2prom requires the [jstat](https://docs.oracle.com/javase/9/tools/jstat.htm#JSWOR734) tool.
It is currently shipped with the JDK. We've been using it with OpenJDK 1.8.0_151, which is part of
the Amazon Linux AMI. It also requires Python 2 (we run it on 2.7.12).
[Prometheus node exporter](https://github.com/prometheus/node_exporter) must be running at the
same machine that is running jstat2prom and `--collector.textfile.directory` should be pointing to
the directory declared by `PROM_DIR` (the default is /tmp).

## Why?
jstat is known to be an experimental and [unsupported tool](https://docs.oracle.com/javase/9/tools/jstat.htm#JSWOR734)
but it has a few advantages over the use of JMX: there is no need to reconfigure the JVM to provide
instrumentation and being a command-line tool, it can easily be parsed and called by a script.

In our use case, we needed to monitor an Elasticsearch cluster for a few JVM metrics
(gc + memory pool usage) and getting them from the Elasticsearch API was not reliable during times where
it became unavailable or unresponsive. Since we were already using Prometheus node exporter on
every node, it was easier to build this tool making use of jstat instead of using JMX.

## Configuration
`PROM_DIR`:  default is /tmp and should point to whatever you have configured with the Prometheus exporter
`METRIC_PREFIX`: default is jstat_metric_name but you can change to something else

List of metrics:
```
jvm_mem_heap_used_bytes gauge
jvm_mem_heap_max_bytes gauge
jvm_mem_non_heap_used_bytes gauge
jvm_mem_non_heap_max_bytes gauge
jvm_mem_pools_young_used_bytes gauge
jvm_mem_pools_young_max_bytes gauge
jvm_mem_pools_old_used_bytes gauge
jvm_mem_pools_old_max_bytes gauge
jvm_gc_collectors_young_collection_count counter
jvm_gc_collectors_young_collection_time_seconds gauge
jvm_gc_collectors_old_collection_count counter
jvm_gc_collectors_old_collection_time_seconds gauge
```

jstat2prom looks for the pid of a java process running in the system using pgrep. If you have more then
one java process running, you may want to look at pgrep to see how you can change the selection criteria.

## Running
Just run `python jstat2prom.py`. It will run forever in a loop until interrupted through Control-C.
Values will be sent to stdout. jstat requires the same user permissions as the one running the JVM.
A file named `jstat.prom` should be written to /tmp.
