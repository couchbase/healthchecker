#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import traceback
import copy
import logging

import listservers
import buckets
#import node
import info
import util_cli as util
import mc_bin_client

import stats_buffer

class StatsCollector:
    def __init__(self, log):
        self.log = log

    def seg(self, k, v):
        # Parse ('some_stat_x_y', 'v') into (('some_stat', x, y), v)
        ka = k.split('_')
        k = '_'.join(ka[0:-1])
        kstart, kend = [int(x) for x in ka[-1].split(',')]
        return ((k, kstart, kend), int(v))

    def write_file(self, filename, info):
        f = open(filename, 'w')
        print >> f, util.pretty_print(info)
        f.close()

    def retrieve_node_stats(self, nodeInfo, nodeStats):
        nodeStats['portDirect'] = nodeInfo['ports']['direct']
        nodeStats['portProxy'] = nodeInfo['ports']['proxy']
        nodeStats['clusterMembership'] = nodeInfo['clusterMembership']
        nodeStats['os'] = nodeInfo['os']
        nodeStats['uptime'] = nodeInfo['uptime']
        nodeStats['version'] = nodeInfo['version']

        #memory
        nodeStats['memory'] = {}
        nodeStats['memory']['allocated'] = nodeInfo['mcdMemoryAllocated']
        nodeStats['memory']['reserved'] = nodeInfo['mcdMemoryReserved']
        nodeStats['memory']['free'] = nodeInfo['memoryFree']
        nodeStats['memory']['quota'] = nodeInfo['memoryQuota']
        nodeStats['memory']['total'] = nodeInfo['memoryTotal']

        #storageInfo
        nodeStats['StorageInfo'] = {}
        if nodeInfo['storageTotals'] is not None:

            #print nodeInfo
            hdd = nodeInfo['storageTotals']['hdd']
            if hdd is not None:
                nodeStats['StorageInfo']['hdd'] = {}
                nodeStats['StorageInfo']['hdd']['free'] = hdd['free']
                nodeStats['StorageInfo']['hdd']['quotaTotal'] = hdd['quotaTotal']
                nodeStats['StorageInfo']['hdd']['total'] = hdd['total']
                nodeStats['StorageInfo']['hdd']['used'] = hdd['used']
                nodeStats['StorageInfo']['hdd']['usedByData'] = hdd['usedByData']
            ram = nodeInfo['storageTotals']['ram']
            if ram is not None:
                nodeStats['StorageInfo']['ram'] = {}
                nodeStats['StorageInfo']['ram']['quotaTotal'] = ram['quotaTotal']
                nodeStats['StorageInfo']['ram']['total'] = ram['total']
                nodeStats['StorageInfo']['ram']['used'] = ram['used']
                nodeStats['StorageInfo']['ram']['usedByData'] = ram['usedByData']
                if ram.has_key('quotaUsed'):
                    nodeStats['StorageInfo']['ram']['quotaUsed'] = ram['quotaUsed']
                else:
                    nodeStats['StorageInfo']['ram']['quotaUsed'] = 0

        #system stats
        nodeStats['systemStats'] = {}
        nodeStats['systemStats']['cpu_utilization_rate'] = nodeInfo['systemStats']['cpu_utilization_rate']
        nodeStats['systemStats']['swap_total'] = nodeInfo['systemStats']['swap_total']
        nodeStats['systemStats']['swap_used'] = nodeInfo['systemStats']['swap_used']

        curr_items = 0
        curr_items_tot = 0
        vb_rep_curr_items = 0
        if nodeInfo['interestingStats'] is not None:
            if nodeInfo['interestingStats'].has_key('curr_items'):
                curr_items = nodeInfo['interestingStats']['curr_items']
            else:
                curr_items = 0
            if nodeInfo['interestingStats'].has_key('curr_items_tot'):
                curr_items_tot = nodeInfo['interestingStats']['curr_items_tot']
            else:
                curr_items_tot = 0
            if nodeInfo['interestingStats'].has_key('vb_replica_curr_items'):
                vb_rep_curr_items = nodeInfo['interestingStats']['vb_replica_curr_items']
            else:
                vb_rep_curr_items = 0

        nodeStats['systemStats']['currentItems'] = curr_items
        nodeStats['systemStats']['currentItemsTotal'] = curr_items_tot
        nodeStats['systemStats']['replicaCurrentItems'] = vb_rep_curr_items

    def get_hostlist(self, server, port, user, password, opts):
        try:
            opts.append(("-o", "return"))
            nodes = listservers.ListServers().runCmd('host-list', server, port, user, password, opts)
            for node in nodes:
                (node_server, node_port) = util.hostport(node['hostname'])
                node_stats = {"host" : node_server,
                          "port" : node_port,
                          "status" : node['status'],
                          "master" : server}
                stats_buffer.nodes[node['hostname']] = node_stats
                if node['status'] == 'healthy':
                    node_info = info.Info().runCmd('get-server-info', node_server, node_port, user, password, opts)
                    self.retrieve_node_stats(node_info, node_stats)
                else:
                    self.log.error("Unhealthy node: %s:%s" %(node_server, node['status']))
            return nodes
        except Exception, err:
            traceback.print_exc()
            sys.exit(1)

    def get_bucketlist(self, server, port, user, password, bucketname, opts):
        try:
            bucketlist = buckets.Buckets().runCmd('bucket-get', server, port, user, password, opts)
            for bucket in bucketlist:
                bucket_name = bucket['name']
                if bucketname == 'all' or bucket_name == bucketname:
                    bucketinfo = {}
                    bucketinfo['name'] = bucket_name
                    bucketinfo['bucketType'] = bucket['bucketType']
                    bucketinfo['authType'] = bucket['authType']
                    bucketinfo['saslPassword'] = bucket['saslPassword']
                    bucketinfo['numReplica'] = bucket['replicaNumber']
                    bucketinfo['ramQuota'] = bucket['quota']['ram']
                    bucketinfo['master'] = server
                    if bucket.has_key('vBucketServerMap'):
                        bucketinfo['vBucketServerMap'] = bucket['vBucketServerMap']
                    else:
                        if bucket['bucketType'] != "memcached":
                            self.log.error("vBucketServerMap doesn't exist from bucket info")
                            self.log.error(bucket)
                        
                    bucketStats = bucket['basicStats']
                    bucketinfo['bucketStats'] = {}
                    for key in bucketStats.iterkeys():
                        bucketinfo['bucketStats'][key] = bucketStats[key]

                    stats_buffer.bucket_info[bucket_name] = bucketinfo

                    # get bucket related stats
                    c = buckets.BucketStats(bucket_name)
                    json = c.runCmd('bucket-stats', server, port, user, password, opts)
                    stats_buffer.buckets_summary[bucket_name] = json
            return bucketlist
        except Exception, err:
            traceback.print_exc()
            sys.exit(1)

    def process_histogram_data(self, histogram_data):
        vals = sorted([self.seg(*kv) for kv in histogram_data.items()])
        dd = {}
        totals = {}
        for s in vals:
            if s[0][2] > util.BIG_VALUE:
                # Ignore the upper bound if it is exemely big
                avg = s[0][1]
            else:
                avg = (s[0][1] + s[0][2]) / 2
            k = s[0][0]
            l = dd.get(k, [])
            l.append((avg, s[1]))
            dd[k] = l
            totals[k] = totals.get(k, 0) + s[1]
        return (dd, totals)

    def get_mc_stats_per_node(self, mc, stats):
        cmd_list = ["timings", "tap", "checkpoint", "memory", ""]
        try:
            for cmd in cmd_list:
                if mc:
                    node_stats = mc.stats(cmd)
                else:
                    node_stats = stats
                if node_stats:
                    if cmd == "timings":
                        dd = {}
                        if mc:
                            dd, totals = self.process_histogram_data(node_stats)
                        else:
                            for key in stats.iterkeys():
                                if key.find("timging_") >= 0:
                                    node_stats = stats[key]
                                    dd, totals = self.process_histogram_data(node_stats)
                                    break
                        if dd:
                            for k in sorted(dd):
                                ccount = 0
                                for lbl,v in dd[k]:
                                    ccount += v * lbl
                                stats[k] = ccount / totals[k]
                        stats["timging_"] = node_stats
                    else:
                        for key, val in node_stats.items():
                            stats[key] = val
        except Exception, err:
            traceback.print_exc()

    def get_mc_stats(self, server, bucketlist, nodes, bucketname):
        for bucket in bucketlist:
            bucket_name = bucket['name']
            if bucketname == 'all' or bucket_name == bucketname:
                self.log.info("bucket: %s" % bucket_name)
                stats_buffer.node_stats[bucket_name] = {}
                if stats_buffer.bucket_info[bucket_name]["bucketType"] == 'memcached':
                    self.log.info("Skip memcached bucket: %s" % bucket_name)
                    continue
                for node in nodes:
                    (node_server, node_port) = util.hostport(node['hostname'])
                    self.log.info("  node: %s %s" % (node_server, node['ports']['direct']))
                    if node['status'] == 'healthy':
                        try:
                            stats = {}
                            mc = mc_bin_client.MemcachedClient(node_server, node['ports']['direct'])
                            if bucket["name"] != "Default":
                                mc.sasl_auth_plain(bucket_name.encode("utf8"), bucket["saslPassword"].encode("utf8"))
                            self.get_mc_stats_per_node(mc, stats)
                            stats_buffer.node_stats[bucket_name][node['hostname']] = stats
                        except Exception, err:
                            #stats_buffer.nodes[node['hostname']]['status'] = 'down'
                            traceback.print_exc()

    def get_mc_stats_fromfile(self, bucketname, collected_buckets, collected_nodes):
        for bucket_name in collected_buckets.iterkeys():
            if bucketname == 'all' or bucket_name == bucketname:
                #stats_buffer.node_stats[bucket_name] = {}
                if stats_buffer.bucket_info[bucket_name]["bucketType"] == 'memcached':
                    self.log.info("Skip memcached bucket: %s" % bucket_name)
                    continue
                for node in collected_nodes.iterkeys():
                    (node_server, node_port) = util.hostport(node)
                    if collected_nodes[node]['status'] == 'healthy':
                        try:
                            self.get_mc_stats_per_node(None, stats_buffer.node_stats[bucket_name][node])
                        except Exception, err:
                            traceback.print_exc()
                            sys.exit(1)

    def get_ns_stats(self, bucketlist, server, port, user, password, bucketname, scale, opts):
        stats_buffer.stats[scale] = stats_buffer.counters
        for bucket in bucketlist:
            bucket_name = bucket['name']
            if bucketname == 'all' or bucket_name == bucketname:
                stats_buffer.buckets[bucket_name] = copy.deepcopy(stats_buffer.stats)
                cmd = 'bucket-node-stats'
                for scale, stat_set in stats_buffer.buckets[bucket_name].iteritems():
                    for stat in stat_set.iterkeys():
                        try :
                            sys.stderr.write('.')
                            self.log.debug("retrieve: %s" % stat)
                            c = buckets.BucketNodeStats(bucket_name, stat, scale)
                            json = c.runCmd('bucket-node-stats', server, port, user, password, opts)
                            stats_buffer.buckets[bucket_name][scale][stat] = json
                        except Exception, err:
                            traceback.print_exc()
                sys.stderr.write('\n')

    def collect_data(self, bucketname, cluster, user, password, inputfile, statsfile, scale, opts):
        if not inputfile:
            server, port = util.hostport(cluster)

            #get node list info
            nodes = self.get_hostlist(server, port, user, password, opts)
            self.log.debug(util.pretty_print(stats_buffer.nodes))

            #get bucket list
            bucketlist = self.get_bucketlist(server, port, user, password, bucketname, opts)
            self.log.debug(util.pretty_print(stats_buffer.bucket_info))
            self.log.debug(util.pretty_print(stats_buffer.buckets_summary))

            #get stats from ep-engine
            self.get_mc_stats(server, bucketlist, nodes, bucketname)
            self.log.debug(util.pretty_print(stats_buffer.node_stats))
        
            #get stats from ns-server
            self.get_ns_stats(bucketlist, server, port, user, password, bucketname, scale, opts)
            self.log.debug(util.pretty_print(stats_buffer.buckets))

            collected_data = {}
            collected_data["scale"] = scale
            collected_data["nodes"] = stats_buffer.nodes
            collected_data["bucket_info"] = stats_buffer.bucket_info
            collected_data["buckets_summary"] = stats_buffer.buckets_summary
            collected_data["node_stats"] = stats_buffer.node_stats
            collected_data["buckets"] = stats_buffer.buckets
            self.write_file(os.path.join('reports', statsfile), collected_data)
        else:
            import json
            json_data=open(inputfile)
            collected_data = json.load(json_data)
            json_data.close()
            stats_buffer.nodes = collected_data["nodes"]
            stats_buffer.bucket_info = collected_data["bucket_info"]
            stats_buffer.buckets_summary = collected_data["buckets_summary"]
            stats_buffer.node_stats = collected_data["node_stats"]
            self.get_mc_stats_fromfile(bucketname,
                                       collected_data["buckets"],
                                       collected_data["nodes"])
            stats_buffer.buckets = collected_data["buckets"]
            scale = collected_data["scale"]
        return scale
