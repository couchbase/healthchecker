import stats_buffer
import util_cli as util

class AvgDiskQueue:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if threshold.has_key("DiskQueueDiagnosis"):
            threshold_val = threshold["DiskQueueDiagnosis"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            #print bucket, stats_info
            disk_queue_avg_error = []
            disk_queue_avg_warn = []
            res = []
            values = stats_info[scale][accessor["counter"]]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            total = []
            for node, vals in nodeStats.iteritems():
                if samplesCount > 0:
                    avg = sum(vals) / samplesCount
                else:
                    avg = 0
                avg = int(avg)
                if avg > threshold_val["high"]:
                    symptom = accessor["symptom"].format(util.number_label(avg), util.number_label(threshold_val["high"]))
                    disk_queue_avg_error.append({"node":node, "level":"red", "value":symptom})
                    res.append((node, {"value":util.number_label(avg), "raw":vals}))
                elif avg > threshold_val["low"]:
                    symptom = accessor["symptom"].format(util.number_label(avg), util.number_label(threshold_val["low"]))
                    disk_queue_avg_warn.append({"node":node, "level":"yellow", "value":symptom})
                    res.append((node, {"value":util.number_label(avg), "raw":vals}))
                else:
                    res.append((node, {"value":util.number_label(avg), "raw":vals}))
                total.append(avg)
            if len(disk_queue_avg_error) > 0:
                res.append(("error", disk_queue_avg_error))
            if len(disk_queue_avg_warn) > 0:
                res.append(("warn", disk_queue_avg_warn))

            if len(nodeStats) > 0:
                rate = sum(total) / len(nodeStats)
                res.append(("total", {"value" : util.number_label(rate),
                                      "raw" : total}))

            result[bucket] = res
        return result

class DiskQueueTrend:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if threshold.has_key("DiskQueueDiagnosis"):
            threshold_val = threshold["DiskQueueDiagnosis"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            trend_error = []
            trend_warn = []
            res = []
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                a, b = util.linreg(timestamps, vals)
                if a > threshold_val["high"]:
                    symptom = accessor["symptom"].format(util.pretty_float(a, 3), threshold_val["high"])
                    trend_error.append({"node":node, "level":"red", "value":symptom})
                    res.append((node, util.pretty_float(a)))
                elif a > threshold_val["low"]:
                    symptom = accessor["symptom"].format(util.pretty_float(a, 3), threshold_val["low"])
                    trend_warn.append({"node":node, "level":"yellow", "value":symptom})
                    res.append((node, util.pretty_float(a)))
            if len(trend_error) > 0:
                res.append(("error", trend_error))
            if len(trend_warn) > 0:
                res.append(("warn", trend_warn))
            result[bucket] = res
        return result

class ReplicationTrend:
    def run(self, accessor, scale, threshold=None):
        result = {}
        cluster = 0
        if threshold.has_key(accessor["name"]):
            threshold_val = threshold[accessor["name"]]
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
                values = stats_info[scale][counter]
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
                    delta = int(replica[1])
                    if accessor["type"] == "percentage" and ratio > threshold_val["percentage"]["high"]:
                        symptom = accessor["symptom"].format(util.pretty_float(ratio), threshold_val["percentage"]["high"])
                        num_error.append({"node":active[0], "value": symptom})
                        res.append((active[0], util.pretty_float(ratio) + "%"))
                    elif accessor["type"] == "number" and delta > threshold_val["number"]["high"]:
                        symptom = accessor["symptom"].format(util.number_label(delta), util.number_label(threshold_val["number"]["high"]))
                        num_error.append({"node":active[0], "value": symptom})
                        res.append((active[0], util.number_label(delta)))
                    elif accessor["type"] == "percentage" and ratio > threshold_val["percentage"]["low"]:
                        symptom = accessor["symptom"].format(util.pretty_float(ratio), threshold_val["percentage"]["low"])
                        num_warn.append({"node":active[0], "value": symptom})
                        res.append((active[0], util.pretty_float(ratio) + "%"))
                    elif accessor["type"] == "number" and delta > threshold_val["number"]["low"]:
                        symptom = accessor["symptom"].format(util.number_label(delta), util.number_label(threshold_val["number"]["low"]))
                        num_warn.append({"node":active[0], "value": symptom})
                        res.append((active[0], util.number_label(delta)))
                active_total += active[1]
                replica_total += replica[1]
            if active_total > 0:
                ratio = replica_total * 100.0 / active_total
                cluster += ratio
                if accessor["type"] == "percentage" and ratio > threshold_val["percentage"]["high"]:
                    symptom = accessor["symptom"].format(util.pretty_float(ratio), threshold_val["percentage"]["high"])
                    num_error.append({"node":"total", "value": symptom})
                    res.append(("total", util.pretty_float(ratio) + "%"))
                elif accessor["type"] == "percentage" and ratio  > threshold_val["percentage"]["low"]:
                    symptom = accessor["symptom"].format(util.pretty_float(ratio), threshold_val["percentage"]["low"])
                    num_warn.append({"node":"total", "value": symptom})
                    res.append(("total", util.pretty_float(ratio) + "%"))
            if len(num_error) > 0:
                res.append(("error", num_error))
            if len(num_warn) > 0:
                res.append(("warn", num_warn))
            result[bucket] = res
        if len(stats_buffer.buckets) > 0:
            result["cluster"] = util.pretty_float(cluster / len(stats_buffer.buckets))
        return result

class DiskQueueDrainingRate:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if threshold.has_key("DiskQueueDrainingAnalysis"):
            threshold_val = threshold["DiskQueueDrainingAnalysis"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            res = []
            disk_queue_avg_error = []
            drain_values = stats_info[scale][accessor["counter"][0]]
            len_values = stats_info[scale][accessor["counter"][1]]
            nodeStats = drain_values["nodeStats"]
            samplesCount = drain_values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                if samplesCount > 0:
                    avg = sum(vals) / samplesCount
                else:
                    avg = 0
                if node in len_values["nodeStats"]:
                    disk_len_vals = len_values["nodeStats"][node]
                else:
                    continue
                if samplesCount > 0:
                    len_avg = sum(disk_len_vals) / samplesCount
                else:
                    len_avg = 0
                if avg < threshold_val["drainRate"] and len_avg > threshold_val["diskLength"]:
                    symptom = accessor["symptom"].format(util.pretty_float(avg), threshold_val["drainRate"], int(len_avg), threshold_val["diskLength"])
                    disk_queue_avg_error.append({"node":node, "level":"red", "value":symptom})
                    res.append((node, (util.pretty_float(avg), int(len_avg))))

            if len(disk_queue_avg_error) > 0:
                res.append(("error", disk_queue_avg_error))
            result[bucket] = res
        return result

DiskQueueCapsule = [
    {"name" : "DiskQueueDiagnosis",
     "description" : "",
     "ingredients" : [
        {
            "name" : "avgDiskQueueLength",
            "description" : "Average disk write queue length",
            "counter" : "disk_write_queue",
            "pernode" : True,
            "scale" : "minute",
            "code" : "AvgDiskQueue",
            "threshold" : {
                "low" : 500000,
                "high" : 1000000
            },
            "symptom" : "Disk write queue length '{0}' has reached '{1}' items",
            "formula" : "Avg(disk_write_queue) > threshold"
        },
        {
            "name" : "diskQueueTrend",
            "description" : "Persistence severely behind - disk write queue continues growing",
            "counter" : "disk_write_queue",
            "pernode" : True,
            "scale" : "hour",
            "code" : "DiskQueueTrend",
            "threshold" : {
                "low" : 0.01,
                "high" : 0.25
            },
            "symptom" : "Disk write queue growing trend '{0}' is above threshold '{1}'",
            "formula" : "Linear(disk_write_queue) > threshold",
        },
     ],
     "indicator" : True,
     "perBucket" : True,
     "perNode" : True,
    },
    {"name" : "ReplicationPercentageTrend",
     "ingredients" : [
        {
            "name" : "replicationPercentageTrend",
            "description" : "Replication backlog size to active item ratio",
            "counter" : ["curr_items", "ep_tap_total_total_backlog_size"],
            "scale" : "hour",
            "code" : "ReplicationTrend",
            "type" : "percentage",
            "threshold" : {
                "percentage" : {
                    "low" : 10.0,
                    "high" : 30.0,
                 },
            },
            "symptom" : "Number of backlog item to active item ratio '{0}%' is above threshold '{1}%'",
            "formula" : "Avg(ep_tap_total_total_backlog_size) / Avg(curr_items) > threshold",
        }
     ],
     "perBucket" : True,
     "indicator" : True,
    },
    {"name" : "ReplicationNumTrend",
     "ingredients" : [
        {
            "name" : "replicationNumTrend",
            "description" : "Replication backlog size",
            "counter" : ["curr_items", "ep_tap_total_total_backlog_size"],
            "scale" : "hour",
            "code" : "ReplicationTrend",
            "type" : "number",
            "threshold" : {
                "number" : {
                    "low" : 50000,
                    "high" : 100000,
                },
            },
            "symptom" : "Number of backlog items '{0}' is above threshold '{1}'",
            "formula" : "Avg(ep_tap_total_total_backlog_size) > threshold",
        }
     ],
     "perBucket" : True,
     "indicator" : True,
    },
    {"name" : "DiskQueueDrainingAnalysis",
     "description" : "",
     "ingredients" : [
        {
            "name" : "activeDiskQueueDrainRate",
            "description" : "Persistence severely behind ",
            "counter" : ["vb_active_queue_drain", "disk_write_queue"],
            "pernode" : True,
            "scale" : "minute",
            "code" : "DiskQueueDrainingRate",
            "threshold" : {
                "drainRate" : 0,
                "diskLength" : 100000,
            },
            "symptom" : "Active disk queue draining rate '{0} is below threshold '{1}' and length '{2}' is bigger than '{3}'",
            "formula" : "Avg(vb_active_queue_drain) < threshold AND Avg(disk_write_queue) > threshold",
        },
        {
            "name" : "replicaDiskQueueDrainRate",
            "description" : "Replication severely behind ",
            "counter" : ["vb_replica_queue_drain", "disk_write_queue"],
            "pernode" : True,
            "scale" : "minute",
            "code" : "DiskQueueDrainingRate",
            "threshold" : {
                "drainRate" : 0,
                "diskLength" : 100000,
            },
            "symptom" : "Replica disk queue draining rate '{0} is below threshold '{1}' and length '{2}' is bigger than '{3}'",
            "formula" : "Avg(vb_replica_queue_drain) < threshold AND Avg(disk_write_queue) > threshold"
        },
     ],
     "indicator" : True,
     "perBucket" : True,
    },
]