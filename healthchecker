#!/usr/bin/python
# -*- coding: utf-8 -*-

import getopt
import sys
import os
import traceback
import copy
import logging

import collector
import analyzer
import stats_buffer
import util_cli as util

import node_map

log = logging.getLogger('healthChecker')
log.setLevel(logging.INFO)
log.addHandler(logging.StreamHandler())

def parse_opt():
    (cluster, user, password, txtfile, htmlfile, verbose) = ('', '', '', 'kpi_report.txt', 'health_report.html', True)

    try:
        (opts, _args) = getopt.getopt(sys.argv[1:], 
                                      'c:dvp:u:t:h:', [
                'cluster=',
                'debug',
                'verbose',
                'password=',
                'user=',
                'txt=',
                'html=',
                ])
    except getopt.GetoptError, err:
        usage(err)

    for (opt, arg) in opts:
        if opt in ('-c', '--cluster'):
            cluster = arg
        if opt in ('-u', '--user'):
            user = arg
        if opt in ('-p', '--password'):
            password = arg
        if opt in ('-d', '--debug'):
            log.setLevel(logging.DEBUG)
        if opt in ('-t', '--txt'):
            txtfile = arg
        if opt in ('-h', '--html'):
            htmlfile = arg

    if not cluster: 
        usage()
    return (cluster, user, password, txtfile, htmlfile, verbose, opts)

def usage(error_msg=''):
    if error_msg:
        print "ERROR: %s" % error_msg
        sys.exit(2)

    print """healthChecker - cluster key performance indicator stats

usage: healthChecker CLUSTER OPTIONS

CLUSTER:
  --cluster=HOST[:PORT] or -c HOST[:PORT]

OPTIONS:
  -u USERNAME, --user=USERNAME      admin username of the cluster
  -p PASSWORD, --password=PASSWORD  admin password of the cluster
  -o FILENAME, --output=FILENAME    Default output filename is 'kpi_report.txt'
  -d --debug
  -v --verbose                      Display detailed node level information
"""
    sys.exit(2)

def main():
    (cluster, user, password, txtfile, htmlfile, verbose, opts) = parse_opt()
    #make snapshot for the current cluster status
    retriever = collector.StatsCollector(log)
    retriever.collect_data(cluster, user, password, opts)

    #analyze the snapshot and historic data
    performer = analyzer.StatsAnalyzer(log)
    performer.run_analysis()
    performer.run_report(txtfile, htmlfile, verbose)

if __name__ == '__main__':
    main()
