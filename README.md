HealthChecker
=============

We use this tool to collect cluster wide couchbase stats and generate health analysis report.

Build
-------

After you clone the project from `git://github.com/couchbase/healthchecker.git`, run the following command:

    config/autorun.sh

To build the package, run

    make bdist

Build on windows
-------

Make sure you install python and py2exe on your build machine

To build the pacakge, run

    make -f Makefile.mingw

Run command
------------

    cbhealthcheck -h

usage: cbhealthchecker CLUSTER USERNAME PASSWORD OPTIONS

CLUSTER:
  --cluster=HOST[:PORT] or -c HOST[:PORT] Default port is 8091
USERNAME:

  `-u USERNAME`, --user=USERNAME       admin username of the cluster
PASSWORD:
  `-p PASSWORD`, --password=PASSWORD   admin password of the cluster
OPTIONS:
  `-b BUCKETNAME`, --bucket=BUCKETNAME Specific bucket name. Default is all buckets
  `-i FILENAME`, --input=FILENAME      Construct report out of input JSON file
  `-o FILENAME`, --output=FILENAME     Default output filename is 'health_report.html'
  `-d` --debug                         Show diagnosis information
  `-h` --help                          Show this help message and exit
  `-v` --verbose                       Display detailed node level information
  `-s SCALE`, --scale=SCALE            Specify stats scale, i.e. minute, hour, day, week, month and year
                                       Default scale is 'day'
  `-j` --jsononly                      Colllect data only but no analysis report generated
