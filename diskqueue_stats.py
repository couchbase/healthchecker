import stats_buffer
import util_cli as util

class AvgDiskQueue:
    def run(self, accessor, threshold=None):
        result = {}
        if threshold.has_key("DiskQueueDiagnosis"):
            threshold_val = threshold["DiskQueueDiagnosis"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            #print bucket, stats_info
            disk_queue_avg_error = []
            disk_queue_avg_warn = []
            values = stats_info[accessor["scale"]][accessor["counter"]]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                if samplesCount > 0:
                    avg = sum(vals) / samplesCount
                else:
                    avg = 0
                if avg > threshold_val["high"]:
                    disk_queue_avg_error.append({"node":node, "level":"red", "value":avg})
                elif avg > threshold_val["low"]:
                    disk_queue_avg_warn.append({"node":node, "level":"yellow", "value":avg})
            if len(disk_queue_avg_error) > 0:
                result[bucket] = {"error" : disk_queue_avg_error}
            if len(disk_queue_avg_warn) > 0:
                result[bucket] = {"warn" : disk_queue_avg_warn}
        return result

class DiskQueueTrend:
    def run(self, accessor, threshold=None):
        result = {}
        if threshold.has_key("DiskQueueDiagnosis"):
            threshold_val = threshold["DiskQueueDiagnosis"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            trend_error = []
            trend_warn = []
            values = stats_info[accessor["scale"]][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                a, b = util.linreg(timestamps, vals)
                if a > threshold_val["high"]:
                    trend_error.append({"node":node, "level":"red", "value":a})
                elif a > threshold_val["low"]:
                    trend_warn.append({"node":node, "level":"yellow", "value":a})
            if len(trend_error) > 0:
                result[bucket] = {"error" : trend_error}
            if len(trend_warn) > 0:
                result[bucket] = {"warn" : trend_warn}
        return result

class ReplicationTrend:
    def run(self, accessor, threshold=None):
        result = {}
        cluster = 0
        if threshold.has_key("ReplicationTrend"):
            threshold_val = threshold["ReplicationTrend"]
        else:
            threshold_val = accessor["threshold"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            item_avg = {
                "curr_items": [],
                "ep_tap_total_total_backlog_size": [],
            }
            num_error = []
            num_warn = []
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
            for active, replica in zip(item_avg['curr_items'], item_avg['ep_tap_total_total_backlog_size']):
                if active[1] == 0:
                    res.append((active[0], 0))
                else:
                    ratio = 100.0 * replica[1] / active[1] 
                    delta = active[1] - replica[1]
                    res.append((active[0], util.pretty_float(ratio)))
                    if (ratio > threshold_val["percentage"]["high"] or 
                       delta > threshold_val["number"]["high"]):
                        num_error.append({"node":active[0], "value": (util.pretty_float(ratio), int(delta))})
                    elif (ratio > threshold_val["percentage"]["low"] or
                         delta > threshold_val["number"]["low"]):
                        num_warn.append({"node":active[0], "value": (util.pretty_float(ratio), int(delta))})
                active_total += active[1]
                replica_total += replica[1]
            if active_total == 0:
                res.append(("total", 0))
            else:
                ratio = replica_total * 100.0 / active_total
                cluster += ratio
                res.append(("total", util.pretty_float(ratio)))
                if ratio > threshold_val["percentage"]["high"]:
                    num_error.append({"node":"total", "value": util.pretty_float(ratio)})
                elif ratio  > threshold_val["percentage"]["low"]:
                    num_warn.append({"node":"total", "value": util.pretty_float(ratio)})
            if len(num_error) > 0:
                res.append(("error", num_error))
            if len(num_warn) > 0:
                res.append(("warn", num_warn))
            result[bucket] = res
        if len(stats_buffer.buckets) > 0:
            result["cluster"] = util.pretty_float(cluster / len(stats_buffer.buckets))
        return result

class DiskQueueDrainingRate:
    def run(self, accessor, threshold=None):
        result = {}
        if threshold.has_key("DiskQueueDrainingAnalysis"):
            threshold_val = threshold["DiskQueueDrainingAnalysis"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            #print bucket, stats_info
            disk_queue_avg_error = []
            disk_queue_avg_warn = []
            drain_values = stats_info[accessor["scale"]][accessor["counter"][0]]
            len_values = stats_info[accessor["scale"]][accessor["counter"][1]]
            nodeStats = drain_values["nodeStats"]
            samplesCount = drain_values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                if samplesCount > 0:
                    avg = sum(vals) / samplesCount
                else:
                    avg = 0
                disk_len_vals = len_values["nodeStats"][node]
                if samplesCount > 0:
                    len_avg = sum(disk_len_vals) / samplesCount
                else:
                    len_avg = 0
                if avg < threshold_val["drainRate"] and len_avg > threshold_val["diskLength"]:
                    disk_queue_avg_error.append({"node":node, "level":"red", "value":avg})
            if len(disk_queue_avg_error) > 0:
                result[bucket] = {"error" : disk_queue_avg_error}
        return result

DiskQueueCapsule = [
    {"name" : "DiskQueueDiagnosis",
     "description" : "",
     "ingredients" : [
        {
            "name" : "avgDiskQueueLength",
            "description" : "Persistence severely behind - averge disk queue length is above threshold",
            "counter" : "disk_write_queue",
            "pernode" : True,
            "scale" : "minute",
            "code" : "AvgDiskQueue",
            "threshold" : {
                "low" : 50000000,
                "high" : 1000000000
            },
        },
        {
            "name" : "diskQueueTrend",
            "description" : "Persistence severely behind - disk write queue continues growing",
            "counter" : "disk_write_queue",
            "pernode" : True,
            "scale" : "hour",
            "code" : "DiskQueueTrend",
            "threshold" : {
                "low" : 0,
                "high" : 0.25
            },
        },
     ],
     "indicator" : {
        "cause" : "Disk write queue backed up",
        "impact" : "Data will be lost if the node goes down",
        "action" : "Please contact support@couchbase.com",
     },
    },
    {"name" : "ReplicationTrend",
     "ingredients" : [
        {
            "name" : "replicationTrend",
            "description" : "Replication severely behind - ",
            "counter" : ["curr_items", "ep_tap_total_total_backlog_size"],
            "scale" : "hour",
            "code" : "ReplicationTrend",
            "threshold" : {
                "percentage" : {
                    "low" : 10.0,
                    "high" : 30.0,
                 },
                "number" : {
                    "low" : 50000,
                    "high" : 100000,
                },
            },
        }
     ],
     "pernode" : True,
     "indicator" : {
        "cause" : "Ratio of items in the replication queue and active items greater than threshold",
        "impact" : "If the nodes fails over, data will be missing on the replica",
        "action" : "Do not failover the node",
     },
    },
     {"name" : "DiskQueueDrainingAnalysis",
     "description" : "",
     "ingredients" : [
        {
            "name" : "activeDiskQueueDrainRate",
            "description" : "Persistence severely behind - active disk queue draining rate is below threshold",
            "counter" : ["vb_active_queue_drain", "disk_write_queue"],
            "pernode" : True,
            "scale" : "minute",
            "code" : "DiskQueueDrainingRate",
            "threshold" : {
                "drainRate" : 0,
                "diskLength" : 100000,
            },
        },
        {
            "name" : "replicaDiskQueueDrainRate",
            "description" : "Persistence severely behind - replica disk queue draining rate is below threshold",
            "counter" : ["vb_replica_queue_drain", "disk_write_queue"],
            "pernode" : True,
            "scale" : "minute",
            "code" : "DiskQueueDrainingRate",
            "threshold" : {
                "drainRate" : 0,
                "diskLength" : 100000,
            },
        },
     ],
     "indicator" : {
        "cause" : "blah",
        "impact" : "blah",
        "action" : "Please contact support@couchbase.com",
     }
    },
]