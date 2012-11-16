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
            values = stats_info[scale][accessor["counter"][0]]
            curr_values = stats_info[scale][accessor["counter"][1]]
            cmdset_values = stats_info[scale][accessor["counter"][2]]
 q
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            timestamps = values["timestamp"]
            total = []
            for node, vals in nodeStats.iteritems():
                curr_vals = curr_values["nodeStats"][node]
                cmdset_vals = cmdset_values["nodeStats"][node]
                if samplesCount > 0:
                    node_avg_dwq = sum(vals) / samplesCount
                    node_avg_curr = sum(curr_vals) / samplesCount
                    node_avg_cmdset = sum(cmdset_vals) / samplesCount
                else:
                    node_avg_curr = 0
                    node_avg_cmdest = 0

                abnormal_segs = util.abnormal_extract(vals, threshold_val["disk_write_queue"]["low"])
                abnormal_vals = []
                for seg in abnormal_segs:
                    begin_index = seg[0]
                    seg_total = seg[1]
                    if seg_total < threshold_val["recurrence"]:
                        continue

                    end_index = begin_index + seg_total
                    cmdset_avg = sum(cmdset_vals[begin_index : end_index]) / seg_total
                    curr_avg = sum(curr_vals[begin_index : end_index]) / seg_total
                    dwq_avg = sum(vals[begin_index : end_index]) / seg_total

                    if curr_avg > node_avg_curr and cmdset_avg > node_avg_cmdset:
                        symptom = accessor["symptom"].format(util.pretty_datetime(timestamps[begin_index]), 
                                                             util.pretty_datetime(timestamps[end_index-1]),
                                                             util.number_label(int(cmdset_avg)),
                                                             util.number_label(int(curr_avg)), 
                                                             util.number_label(dwq_avg))
                        abnormal_vals.append(dwq_avg)
                        if dwq_avg > threshold_val["disk_write_queue"]["high"]:
                            disk_queue_avg_error.append({"node":node, "value":symptom})
                        else:
                            disk_queue_avg_warn.append({"node":node, "level":"yellow", "value":symptom})
                if len(abnormal_vals) > 0:
                    res.append((node, {"value":util.number_label(dwq_avg), "raw":abnormal_vals}))
                total.append(node_avg_dwq)
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

class PerformanceDiagnosis_diskread:
    def run(self, accessor, scale, threshold=None):
        result = {}
        thresholdval = accessor["threshold"]
        if threshold.has_key("PerformanceDiagnosis_one"):
            thresholdval = threshold["PerformanceDiagnosis_one"]

        for bucket, stats_info in stats_buffer.buckets.iteritems():
            if stats_info[scale].get(accessor["counter"][0], None) is None:
                return result

            diskRead_values = stats_info[scale][accessor["counter"][0]]
            cacheMissRate_values = stats_info[scale][accessor["counter"][1]]
            arr_values = stats_info[scale][accessor["counter"][2]]
            memUsed_values = stats_info[scale][accessor["counter"][3]]
            curr_values = stats_info[scale][accessor["counter"][4]]
            cmdSet_values = stats_info[scale][accessor["counter"][5]]

            timestamps = diskRead_values["timestamp"]
            samplesCount = diskRead_values["samplesCount"]

            trend = []
            num_warn = []
            for node, vals in diskRead_values["nodeStats"].iteritems():
                diskRead_vals = diskRead_values["nodeStats"][node]
                cacheMissRate_vals = cacheMissRate_values["nodeStats"][node]
                arr_vals = arr_values["nodeStats"][node]
                memUsed_vals = memUsed_values["nodeStats"][node]
                curr_vals = curr_values["nodeStats"][node]
                cmdSet_vals = cmdSet_values["nodeStats"][node]
                if samplesCount > 0:
                    node_avg_mem = sum(memUsed_vals) / samplesCount
                    node_avg_curr = sum(curr_vals) / samplesCount
                    node_avg_cmdset = sum(cmdSet_vals) / samplesCount
                else:
                    node_avg_curr = 0
                # Fine grained analysis
                abnormal_segs = util.abnormal_extract(diskRead_vals, thresholdval["ep_cache_miss_rate"])
                abnormal_vals = []
                for seg in abnormal_segs:
                    begin_index = seg[0]
                    seg_total = seg[1]
                    if seg_total < thresholdval["recurrence"]:
                        continue
                    end_index = begin_index + seg_total

                    diskread_avg = sum(diskRead_vals[begin_index : end_index]) / seg_total
                    cmr_avg = sum(cacheMissRate_vals[begin_index : end_index]) / seg_total
                    arr_avg = sum(arr_vals[begin_index : end_index]) / seg_total
                    mem_avg = sum(memUsed_vals[begin_index : end_index]) / seg_total
                    curr_avg = sum(curr_vals[begin_index : end_index]) / seg_total
                    cmdSet_avg = sum(cmdSet_values[begin_index : end_index]) / seg_total

                    if cmr_avg > thresholdval["ep_cache_miss_rate"] and \
                       arr_avg < thresholdval["vb_active_resident_items_ratio"] and \
                       mem_avg > node_avg_mem and \
                       curr_avg > node_avg_curr and \
                       cmdSet_avg > node_avg_cmdset:
                        symptom = accessor["symptom"].format(util.pretty_datetime(timestamps[begin_index]), 
                                                             util.pretty_datetime(timestamps[end_index-1]),
                                                             util.number_label(int(cmdSet_avg)),
                                                             util.number_label(int(curr_avg)),
                                                             util.number_label(int(mem_avg)),
                                                             util.pretty_float(cmr_avg), 
                                                             util.pretty_float(arr_avg),
                                                             util.number_label(int(diskread_avg)))
                        num_warn.append({"node":node, "value":symptom})
                        abnormal_vals.append(diskread_avg)
                if len(abnormal_vals) > 0:
                    trend.append((node, {"value" : util.pretty_float(sum(abnormal_vals)/len(abnormal_vals)) + "%",
                                         "raw" : abnormal_vals}
                                    ))
            if len(num_warn) > 0:
                trend.append(("warn", num_warn))
            result[bucket] = trend

        return result

DiskQueueCapsule = [
    {"name" : "DiskQueueDiagnosis",
     "description" : "",
     "ingredients" : [
        {
            "name" : "avgDiskQueueLength",
            "description" : "Average disk write queue length",
            "counter" : ["disk_write_queue", "curr_items", "cmd_set"],
            "scale" : "minute",
            "code" : "AvgDiskQueue",
            "threshold" : {
                "disk_write_queue" : {"low" : 500000, "high" : 1000000 },
                "recurrence" : 10,
            },
            "symptom" : "From {0} to {1}, a higher set/sec '{2}' leads to high item count '{3}' and long disk write queue length '{4}'",
            "formula" : "Avg(disk_write_queue) > threshold"
        },
        {
            "name" : "diskQueueTrend",
            "description" : "Persistence severely behind - disk write queue continues growing",
            "counter" : "disk_write_queue",
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
    {"name" : "PerformanceDiagnosis_diskread",
     "ingredients" : [
        {
            "name" : "performanceDiagnosis_diskread",
            "description" : "Diagnosis lots of disk reads",
            "symptom" : "From {0} to {1}, a high sets/sec jump '{2}' leads to a higher item count '{3}', high memory used '{4}, " \
                        "high cache miss ratio '{5}%', low residential ratio '{6}%' and lots of disk reads '{7}'.",
            "counter" : ["ep_bg_fetched","ep_cache_miss_rate", "vb_active_resident_items_ratio", "mem_used", "curr_items", "cmd_set"],
            "code" : "PerformanceDiagnosis_diskread",
            "threshold" : {
                "ep_bg_fetched" : 50, # lots of disk reads
                "ep_cache_miss_rate" : 2, # 2%  high
                "vb_active_resident_items_ratio" : 30, # low 
                "recurrence" : 10
            },
            "formula" : "Avg(ep_cache_miss_rate)",
        },
     ],
     "clusterwise" : False,
     "perNode" : True,
     "perBucket" : True,
     "indicator" : True,
     "nodeDisparate" : True,
    },
]