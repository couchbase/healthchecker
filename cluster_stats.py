import stats_buffer
import util_cli as util

class BucketSummary:
    def run(self, accessor):
        return  stats_buffer.bucket_info

class DGMRatio:
    def run(self, accessor):
        result = []
        hdd_total = 0
        ram_total = 0
        for node, nodeinfo in stats_buffer.nodes.iteritems():
            if nodeinfo["StorageInfo"].has_key("hdd"):
                hdd_total += nodeinfo['StorageInfo']['hdd']['usedByData']
            if nodeinfo["StorageInfo"].has_key("ram"):
                ram_total += nodeinfo['StorageInfo']['ram']['usedByData']
        if ram_total > 0:
            ratio = hdd_total * 1.0 / ram_total
        else:
            ratio = 0
        return util.pretty_float(ratio)

class ARRatio:
    def run(self, accessor):
        result = {}
        cluster = 0
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            item_avg = {
                "curr_items": [],
                "vb_replica_curr_items": [],
            }
            num_error = []
            for counter in accessor["counter"]:
                values = stats_info[accessor["scale"]][counter]
                nodeStats = values["nodeStats"]
                samplesCount = values["samplesCount"]
                for node, vals in nodeStats.iteritems():
                    if samplesCount > 0:
                        avg = sum(vals) / samplesCount
                    else:
                        avg = 0
                    item_avg[counter].append((node, avg))
            res = []
            active_total = replica_total = 0
            for active, replica in zip(item_avg['curr_items'], item_avg['vb_replica_curr_items']):
                if replica[1] == 0:
                    res.append((active[0], "No replica"))
                else:
                    ratio = 1.0 * active[1] / replica[1]
                    res.append((active[0], util.pretty_float(ratio)))
                    if ratio < accessor["threshold"] and abs(ratio - accessor["threshold"]) > 1e-2:
                        num_error.append({"node":active[0], "value": util.pretty_float(ratio)})
                active_total += active[1]
                replica_total += replica[1]
            if replica_total == 0:
                res.append(("total", "no replica"))
            else:
                ratio = active_total * 1.0 / replica_total
                cluster += ratio
                res.append(("total", util.pretty_float(ratio)))
                if ratio < accessor["threshold"] and abs(ratio - accessor["threshold"]) > 1e-2:
                    num_error.append({"node":"total", "value": util.pretty_float(ratio)})
            if len(num_error) > 0:
                res.append(("error", num_error))
            result[bucket] = res
        if len(stats_buffer.buckets) > 0:
            result["cluster"] = util.pretty_float(cluster / len(stats_buffer.buckets))
        return result

class OpsRatio:
    def run(self, accessor):
        result = {}
        read_cluster = write_cluster = del_cluster = 0
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            ops_avg = {
                "cmd_get": [],
                "cmd_set": [],
                "delete_hits" : [],
            }
            for counter in accessor["counter"]:
                values = stats_info[accessor["scale"]][counter]
                nodeStats = values["nodeStats"]
                samplesCount = values["samplesCount"]
                for node, vals in nodeStats.iteritems():
                    if samplesCount > 0:
                        avg = sum(vals) / samplesCount
                    else:
                        avg = 0
                    ops_avg[counter].append((node, avg))
            res = []
            read_total = write_total = del_total = 0
            for read, write, delete in zip(ops_avg['cmd_get'], ops_avg['cmd_set'], ops_avg['delete_hits']):
                count = read[1] + write[1] + delete[1]
                if count == 0:
                    res.append((read[0], "0% reads : 0% writes : 0% deletes"))
                else:
                    read_ratio = read[1] *100.0 / count
                    read_total += read_ratio
                    write_ratio = write[1] * 100.0 / count
                    write_total += write_ratio
                    del_ratio = delete[1] * 100.0 / count
                    del_total += del_ratio
                    res.append((read[0], "{0}% reads : {1}% writes : {2}% deletes".format(int(read_ratio+.5), int(write_ratio+.5), int(del_ratio+.5))))
                    read_cluster += read[1]
                    write_cluster += write[1]
                    del_cluster += delete[1]

            if len(ops_avg['cmd_get']) > 0:
                read_total /= len(ops_avg['cmd_get'])
            if len(ops_avg['cmd_set']) > 0:
                write_total /= len(ops_avg['cmd_set'])
            if len(ops_avg['delete_hits']) > 0:
                del_total /= len(ops_avg['delete_hits'])
            res.append(("total", "{0}% reads : {1}% writes : {2}% deletes".format(int(read_total+.5), int(write_total+.5), int(del_total+.5))))
            result[bucket] = res
        count = read_cluster + write_cluster + del_cluster
        if count == 0:
            read_ratio = write_ratio = del_ratio = 0
        else:
            read_ratio = read_cluster * 100.0 / count + .5
            write_ratio = write_cluster * 100.0 / count + .5
            del_ratio = del_cluster * 100 / count + .5
        result["cluster"] = "{0}% reads : {1}% writes : {2}% deletes".format(int(read_ratio), int(write_ratio), int(del_ratio))
        return result

class CacheMissRatio:
    def run(self, accessor):
        result = {}
        cluster = 0
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[accessor["scale"]][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            total = 0
            data = []
            num_error = []
            for node, vals in nodeStats.iteritems():
                #a, b = util.linreg(timestamps, vals)
                if samplesCount > 0:
                    value = sum(vals) / samplesCount
                else:
                    value = 0
                total += value
                if value > accessor["threshold"]:
                    num_error.append({"node":node, "value":value})
                trend.append((node, util.pretty_float(value) + "%"))
                data.append(value)
            if len(nodeStats) > 0:
                total /= len(nodeStats)
            trend.append(("total", util.pretty_float(total) + "%"))
            trend.append(("variance", util.two_pass_variance(data)))
            if len(num_error) > 0:
                trend.append(("error", num_error))
            cluster += total
            result[bucket] = trend
        if len(stats_buffer.buckets) > 0:
            result["cluster"] = util.pretty_float(cluster / len(stats_buffer.buckets)) + "%"
        return result

class ResidentItemRatio:
    def run(self, accessor):
        result = {}
        cluster = 0
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[accessor["scale"]][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            total = 0
            data = []
            num_error = []
            for node, vals in nodeStats.iteritems():
                #a, b = util.linreg(timestamps, vals)
                if samplesCount > 0:
                    value = sum(vals) / samplesCount
                else:
                    value = 0
                total += value
                if value < accessor["threshold"]:
                    num_error.append({"node":node, "value":value})
                trend.append((node, util.pretty_float(value) + "%"))
                data.append(value)
            if len(nodeStats) > 0:
                total /= len(nodeStats)
            trend.append(("total", util.pretty_float(total)))
            trend.append(("variance", util.two_pass_variance(data)))
            if len(num_error) > 0:
                trend.append(("error", num_error))
            cluster += total
            result[bucket] = trend
        if len(stats_buffer.buckets) > 0:
            result["cluster"] = util.pretty_float(cluster / len(stats_buffer.buckets)) + "%"
        return result

class MemUsed:
    def run(self, accessor):
        result = {}
        cluster = 0
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[accessor["scale"]][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            total = 0
            data = []
            for node, vals in nodeStats.iteritems():
                if samplesCount > 0:
                    avg = sum(vals) / samplesCount
                else:
                    avg = 0
                trend.append((node, util.size_label(avg)))
                data.append(avg)
            #print data
            trend.append(("variance", util.two_pass_variance(data)))
            result[bucket] = trend
        return result

class ItemGrowth:
    def run(self, accessor):
        result = {}
        start_cluster = 0
        end_cluster = 0
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            trend = []
            values = stats_info[accessor["scale"]][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                a, b = util.linreg(timestamps, vals)
                if b < 1:
                   trend.append((node, 0))
                else:
                    start_val = b
                    start_cluster += b
                    end_val = a * timestamps[-1] + b
                    end_cluster += end_val
                    if b > 0:
                        rate = (end_val * 1.0 / b - 1.0) * 100
                    else:
                        rate = 0
                    trend.append((node, util.pretty_float(rate) + "%"))
            result[bucket] = trend
        if len(stats_buffer.buckets) > 0:
            if start_cluster > 0:
                rate = (end_cluster * 1.0 / start_cluster - 1.0) * 100
            else:
                rate = 0
            result["cluster"] = util.pretty_float(rate) + "%"
        return result

class NumVbuckt:
    def run(self, accessor):
        result = {}
        num_node = len(stats_buffer.nodes)
        if num_node == 0:
            return result
        avg_threshold = accessor["threshold"] / num_node
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            num_error = []
            values = stats_info[accessor["scale"]][accessor["counter"]]
            nodeStats = values["nodeStats"]
            for node, vals in nodeStats.iteritems():
                if vals[-1] < avg_threshold:
                    num_error.append({"node":node, "value": int(vals[-1])})
            if len(num_error) > 0:
                result[bucket] = {"error" : num_error}
        return result

class RebalanceStuck:
    def run(self, accessor):
        result = {}
        err_msg = "{0} value {1} is bigger than threshold {3}"
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            num_error = []
            for node, stats_info in bucket_stats.iteritems():
                for key, value in stats_info.iteritems():
                    if key.find(accessor["counter"]) >= 0:
                        if accessor.has_key("threshold"):
                            if int(value) > accessor["threshold"]:
                                num_error.append({"node":node, "value": err_msg.format(key, value, accessor["threshold"])})
            if len(num_error) > 0:
                result[bucket] = {"error" : num_error}
        return result

class MemoryFramentation:
    def run(self, accessor):
        result = {}
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            num_error = []
            for node, stats_info in bucket_stats.iteritems():
                for key, value in stats_info.iteritems():
                    if key.find(accessor["counter"]) >= 0:
                        if accessor.has_key("threshold"):
                            if int(value) > accessor["threshold"]:
                                if accessor.has_key("unit"):
                                    if accessor["unit"] == "time":
                                        num_error.append({"node":node, "value": (key, util.time_label(value))})
                                    elif accessor["unit"] == "size":
                                        num_error.append({"node":node, "value": (key, util.size_label(value))})
                                    else:
                                        num_error.append({"node":node, "value": (key, value)})
                                else:
                                    num_error.append({"node":node, "value": (key, value)})
            if len(num_error) > 0:
                result[bucket] = {"error" : num_error}
        return result

class EPEnginePerformance:
    def run(self, accessor):
        result = {}
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            num_error = []
            for node, stats_info in bucket_stats.iteritems():
                for key, value in stats_info.iteritems():
                    if key.find(accessor["counter"]) >= 0:
                        if accessor.has_key("threshold"):
                            if accessor["counter"] == "flusherState" and value != accessor["threshold"]:
                                num_error.append({"node":node, "value": (key, value)})
                            elif accessor["counter"] == "flusherCompleted" and value == accessor["threshold"]:
                                num_error.append({"node":node, "value": (key, value)})
                            else:
                                if value > accessor["threshold"]:
                                     num_error.append({"node":node, "value": (key, value)})
            if len(num_error) > 0:
                result[bucket] = {"error" : num_error}
        return result

class TotalDataSize:
    def run(self, accessor):
        total = 0
        for node, nodeinfo in stats_buffer.nodes.iteritems():
            if nodeinfo["StorageInfo"].has_key("hdd"):
                total += nodeinfo['StorageInfo']['hdd']['usedByData']
        return util.size_label(total)

class AvailableDiskSpace:
    def run(self, accessor):
        result = []
        total = 0
        for node, nodeinfo in stats_buffer.nodes.iteritems():
            if nodeinfo["StorageInfo"].has_key("hdd"):
                total += nodeinfo['StorageInfo']['hdd']['free']
        return util.size_label(total)

ClusterCapsule = [
    {"name" : "TotalDataSize",
     "ingredients" : [
        {
            "name" : "totalDataSize",
            "description" : "Total data size across cluster",
            "code" : "TotalDataSize",
        }
     ],
     "clusterwise" : True,
     "perNode" : False,
     "perBucket" : False,
    },
    {"name" : "AvailableDiskSpace",
     "ingredients" : [
        {
            "name" : "availableDiskSpace",
            "description" : "Available disk space",
            "code" : "AvailableDiskSpace",
        }
     ],
     "clusterwise" : True,
     "perNode" : False,
     "perBucket" : False,
    },
   {"name" : "CacheMissRatio",
     "ingredients" : [
        {
            "name" : "cacheMissRatio",
            "description" : "Cache miss ratio",
            "counter" : "ep_cache_miss_rate",
            "scale" : "hour",
            "code" : "CacheMissRatio",
            "threshold" : 2,
        },
     ],
     "clusterwise" : True,
     "perNode" : True,
     "perBucket" : True,
     "indicator" : {
        "cause" : "Cache miss ratio is too high.",
        "impact" : "blah",
        "action" : "Please contact support@couchbase.com",
     },
     "nodeDisparate" : True,
    },
    {"name" : "DGM",
     "ingredients" : [
        {
            "name" : "dgm",
            "description" : "Disk to memory ratio",
            "code" : "DGMRatio"
        },
     ],
     "clusterwise" : True,
     "perNode" : False,
     "perBucket" : False,
    },
    {"name" : "ActiveReplicaResidentRatio",
     "ingredients" : [
        {
            "name" : "activeReplicaResidentRatio",
            "description" : "Active to replica resident ratio",
            "counter" : ["curr_items", "vb_replica_curr_items"],
            "scale" : "minute",
            "code" : "ARRatio",
            "threshold" : 1,
        },
        {
            "name" : "activeResidentRatio",
            "description" : "Active resident ratio",
            "counter" : "vb_active_resident_items_ratio",
            "scale" : "minute",
            "code" : "ResidentItemRatio",
            "threshold" : 30,
        },
        {
            "name" : "replicaResidentRatio",
            "description" : "Replica resident ratio",
            "counter" : "vb_replica_resident_items_ratio",
            "scale" : "minute",
            "code" : "ResidentItemRatio",
            "threshold" : 30,
        },
     ],
     "clusterwise" : True,
     "perNode" : True,
     "perBucket" : True,
     "indicator" : {
        "cause" : "blah",
        "impact" : "blah",
        "action" : "Please contact support@couchbase.com",
     },
    },
    {"name" : "OPSPerformance",
     "ingredients" : [
        {
            "name" : "opsPerformance",
            "description" : "Read/Write/Delete ops ratio",
            "scale" : "minute",
            "counter" : ["cmd_get", "cmd_set", "delete_hits"],
            "code" : "OpsRatio",
        },
     ],
     "perBucket" : True,
     "clusterwise" : True,
    },
    {"name" : "GrowthRate",
     "ingredients" : [
        {
            "name" : "dataGrowthRateForItems",
            "description" : "Data growth rate for items",
            "counter" : "curr_items",
            "scale" : "day",
            "code" : "ItemGrowth",
            "unit" : "percentage",
        },
     ],
     "clusterwise" : True,
    },
    {"name" : "VBucketNumber",
     "ingredients" : [
        {
            "name" : "activeVbucketNumber",
            "description" : "Active VBucket number is less than expected",
            "counter" : "vb_active_num",
            "scale" : "hour",
            "code" : "NumVbuckt",
            "threshold" : 1024,
        },
        {
            "name" : "replicaVBucketNumber",
            "description" : "Replica VBucket number is less than expected",
            "counter" : "vb_replica_num",
            "scale" : "hour",
            "code" : "NumVbuckt",
            "threshold" : 1024,
        },
     ],
     "indicator" : {
        "cause" : "blah",
        "impact" : "blah",
        "action" : "Please contact support@couchbase.com",
     },
    },
    {"name" : "MemoryUsage",
     "ingredients" : [
        {
            "name" : "memoryUsage",
            "description" : "Check memory usage",
            "counter" : "mem_used",
            "scale" : "hour",
            "code" : "MemUsed",
        },
     ],
     "nodeDisparate" : True,
    },
    {"name" : "RebalancePerformance",
     "ingredients" : [
        {
            "name" : "highBackfillRemaing",
            "description" : "Tap queue backfilll remaining is too high",
            "counter" : "ep_tap_queue_backfillremaining",
            "code" : "RebalanceStuck",
            "threshold" : 1000,
        },
        {
            "name" : "tapNack",
            "description" : "Number of nacks",
            "counter" : "num_tap_nack",
            "code" : "RebalanceStuck",
            "threshold" : 5,
        },
     ],
     "indicator" : {
        "cause" : "Tap queue backfill remaining is higher than threshold.",
        "impact" : "blah",
        "action" : "Please contact support@couchbase.com",
     }
    },
    {"name" : "MemoryFragmentation",
     "ingredients" : [
        {
            "name" : "totalFragmentation",
            "description" : "Total memory fragmentation",
            "counter" : "total_fragmentation_bytes",
            "code" : "MemoryFramentation",
            "unit" : "size",
            "threshold" : 1073741824,  # 1GB
        },
        {
            "name" : "diskDelete",
            "description" : "Averge disk delete time",
            "counter" : "disk_del",
            "code" : "MemoryFramentation",
            "unit" : "time",
            "threshold" : 1000     #1ms
        },
        {
            "name" : "diskUpdate",
            "description" : "Averge disk update time",
            "counter" : "disk_update",
            "code" : "MemoryFramentation",
            "unit" : "time",
            "threshold" : 1000     #1ms
        },
        {
            "name" : "diskInsert",
            "description" : "Averge disk insert time",
            "type" : "python",
            "counter" : "disk_insert",
            "code" : "MemoryFramentation",
            "unit" : "time",
            "threshold" : 1000     #1ms
        },
        {
            "name" : "diskCommit",
            "description" : "Averge disk commit time",
            "counter" : "disk_commit",
            "code" : "MemoryFramentation",
            "unit" : "time",
            "threshold" : 5000000     #10s
        },
     ],
     "indicator" : {
        "cause" : "Severe IO issue possibly caused by fragmentation",
        "impact" : "blah",
        "action" : "Please contact support@couchbase.com",
     },
    },
    {"name" : "EPEnginePerformance",
     "ingredients" : [
        {
            "name" : "flusherState",
            "description" : "Engine flusher state",
            "counter" : "ep_flusher_state",
            "code" : "EPEnginePerformance",
            "threshold" : "running",
        },
        {
            "name" : "flusherCompleted",
            "description" : "Flusher completed",
            "counter" : "ep_flusher_num_completed",
            "code" : "EPEnginePerformance",
            "threshold" : 0
        },
        {
            "name" : "avgItemLoadTime",
            "description" : "Average item loaded time",
            "counter" : "ep_bg_load_avg",
            "code" : "EPEnginePerformance",
            "threshold" : 100,
        },
        {
            "name" : "avgItemWaitTime",
            "description" : "Averge item waited time",
            "counter" : "ep_bg_wait_avg",
            "code" : "EPEnginePerformance",
            "threshold" : 100
        },
     ],
     "indicator" : {
        "cause" : "Poor engine KPIs",
        "impact" : "blah",
        "action" : "Please contact support@couchbase.com",
     },
    },
]
