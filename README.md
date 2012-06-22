HealthChecker
=============

We use this tool to collect cluster wide couchbase stats and generate health analysis report.

Build
-------

After you clone the project from `git://github.com/couchbase/healthchecker.git`, run the following command:

    config/autorun.sh

To build the package, run

    make bdist


Run command
------------

    cbhealthcheck -c 10.101.10.1:8091 -u Administrator -p password -v

where `10.101.10.1` is the ipaddress of a node in the cluster, `Administrator` is the admin username of the cluster,
`password` is the admin password of the cluster. `-v` means that you want to show the detail node information.
