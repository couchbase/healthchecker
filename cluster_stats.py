import stats_buffer
import util_cli as util

class DGMRatio:
    def run(self, accessor, scale, threshold=None):
        result = []
        hdd_total = 0
        ram_total = 0
        for node, nodeinfo in stats_buffer.nodes.iteritems():
            if nodeinfo["status"] != "healthy":
                continue
            if nodeinfo["StorageInfo"].has_key("hdd"):
                hdd_total += nodeinfo['StorageInfo']['hdd']['usedByData']
            if nodeinfo["StorageInfo"].has_key("ram"):
                ram_total += nodeinfo['StorageInfo']['ram']['usedByData']
        if ram_total > 0:
            ratio = hdd_total * 100.0 / ram_total
        else:
            ratio = 0
        return {"value" : util.pretty_float(ratio) + "%",
                "raw" : (hdd_total, ram_total)}

class ARRatio:
    def run(self, accessor, scale, threshold=None):
        result = {}
        cluster = []
        if threshold.has_key("ActiveReplicaResidentRatio"):
            threshold_val = threshold["ActiveReplicaResidentRatio"]["activeReplicaResidentRatio"]
        else:
            threshold_val = accessor["threshold"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            item_avg = {
                "curr_items": [],
                "vb_replica_curr_items": [],
            }
            num_error = []
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
            for active, replica in zip(item_avg['curr_items'], item_avg['vb_replica_curr_items']):
                if replica[1] == 0:
                    if active[1] == 0:
                        res.append((active[0], "No active items"))
                    else:
                        res.append((active[0], "No replica"))
                else:
                    ratio = 100.0 * active[1] / replica[1]
                    res.append((active[0], {"value" : util.pretty_float(ratio) + "%", 
                                            "raw" : (active[1],replica[1]),
                                           }))
                active_total += active[1]
                replica_total += replica[1]
            if active_total == 0:
                res.append(("total", "no active items"))
            elif replica_total == 0:
                res.append(("total", "no replica items"))
                if stats_buffer.bucket_info[bucket]["bucketType"] != 'memcached':
                    num_error.append({"node":"total", "value": "No replica items"})
            else:
                ratio = active_total * 100.0 / replica_total
                cluster.append(ratio)
                res.append(("total", {"value" : util.pretty_float(ratio) + "%",
                                      "raw" : (active_total, replica_total)}))
                delta = abs(100 - ratio)
                if delta > threshold_val:
                    symptom = accessor["symptom"].format(util.pretty_float(delta), util.pretty_float(threshold_val))
                    num_error.append({"node":"total", "value": symptom})
            if len(num_error) > 0:
                res.append(("error", num_error))
            result[bucket] = res
        if len(stats_buffer.buckets) > 0:
            result["cluster"] = {"value" : util.pretty_float(sum(cluster) / len(stats_buffer.buckets)) + "%",
                                 "raw" : cluster}
        return result

class OpsRatio:
    def run(self, accessor, scale, threshold=None):
        result = {}
        read_cluster = []
        write_cluster = []
        del_cluster = []
        read_stats = []
        write_stats = []
        del_stats = []
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            ops_avg = {
                "cmd_get": [],
                "cmd_set": [],
                "delete_hits" : [],
            }
            for counter in accessor["counter"]:
                values = stats_info[scale][counter]
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
                    res.append((read[0], {"value":"{0}% reads : {1}% writes : {2}% deletes".format(int(read_ratio+.5), int(write_ratio+.5), int(del_ratio+.5)),
                                          "raw":(read[1], write[1], delete[1]),
                                         }))
                    read_cluster.append(read[1])
                    write_cluster.append(write[1])
                    del_cluster.append(delete[1])

            if len(ops_avg['cmd_get']) > 0:
                read_total /= len(ops_avg['cmd_get'])
            if len(ops_avg['cmd_set']) > 0:
                write_total /= len(ops_avg['cmd_set'])
            if len(ops_avg['delete_hits']) > 0:
                del_total /= len(ops_avg['delete_hits'])
            count = read_total + write_total + del_total
            if count == 0:
                read_ratio = write_ratio = del_ratio = 0
            else:
                read_ratio = read_total * 100.0 / count + .5
                write_ratio = write_total * 100.0 / count + .5
                del_ratio = del_total * 100.0 / count + .5
            res.append(("total", {"value" :"{0}% reads : {1}% writes : {2}% deletes".format(int(read_ratio), int(write_ratio), int(del_ratio)),
                                  "raw" : (read_total, write_total, del_total)}))
            read_stats.append(read_total)
            write_stats.append(write_total)
            del_stats.append(del_total)
            result[bucket] = res

        count = sum(read_cluster) + sum(write_cluster) + sum(del_cluster)
        if count == 0:
            read_ratio = write_ratio = del_ratio = 0
        else:
            read_ratio = sum(read_cluster) * 100.0 / count + .5
            write_ratio = sum(write_cluster) * 100.0 / count + .5
            del_ratio = sum(del_cluster) * 100 / count + .5
        result["cluster"] = {"value" : "{0}% reads : {1}% writes : {2}% deletes".format(int(read_ratio), int(write_ratio), int(del_ratio)),
                             "raw" : (read_stats, write_stats, del_stats)}
        return result

class CacheMissRatio:
    def run(self, accessor, scale, threshold=None):
        result = {}
        cluster = []
        thresholdval = accessor["threshold"]
        if threshold.has_key("CacheMissRatio"):
            thresholdval = threshold["CacheMissRatio"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            total = []
            data = []
            num_error = []
            for node, vals in nodeStats.iteritems():
                #a, b = util.linreg(timestamps, vals)
                if samplesCount > 0:
                    value = sum(vals) / samplesCount
                else:
                    value = 0
                value = max(0, value)
                total.append(value)
                if value > thresholdval:
                    symptom = accessor["symptom"].format(util.pretty_float(value), thresholdval)
                    num_error.append({"node":node, "value":symptom})
                trend.append((node, {"value" : util.pretty_float(value) + "%",
                                     "raw" : vals,
                                    }))
                data.append(value)
            if len(nodeStats) > 0:
                trend.append(("total", {"value" : util.pretty_float(sum(total) / len(nodeStats)) + "%",
                                        "raw" : total}))
            else:
                trend.append(("total", util.pretty_float(sum(total)) + "%"))
            trend.append(("variance", util.two_pass_variance(data)))
            if len(num_error) > 0:
                trend.append(("error", num_error))

            cluster.append(sum(total))
            result[bucket] = trend
        if len(stats_buffer.buckets) > 0:
            result["cluster"] = {"value" : util.pretty_float(sum(cluster) / len(stats_buffer.buckets)) + "%",
                                 "raw" : cluster}
        return result

class ResidentItemRatio:
    def run(self, accessor, scale, threshold=None):
        result = {}
        cluster = []
        if threshold.has_key("ActiveReplicaResidentRatio"):
            threshold_val = threshold["ActiveReplicaResidentRatio"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            total = []
            data = []
            num_error = []
            for node, vals in nodeStats.iteritems():
                a, b = util.linreg(timestamps, vals)
                if len(vals) > 0:
                    # Take the lastest one as sample value
                    value = vals[-1]
                else:
                    value = 0
                total.append(value)
                if value > 0 and value < threshold_val:
                    symptom = accessor["symptom"].format(util.pretty_float(value) + "%", util.pretty_float(threshold_val) + "%")
                    num_error.append({"node":node, "value":symptom})
                trend.append((node, {"value" : util.pretty_float(value) + "%",
                                     "raw" : (samplesCount, vals),
                                    }))
                data.append(value)
            if len(nodeStats) > 0:
                total_val = sum(total) / len(nodeStats)
                cluster.append(total_val)
                trend.append(("total", {"value" : util.pretty_float(total_val) + "%", "raw" : total}))
                if total_val > 0 and total_val < threshold_val:
                    symptom = accessor["symptom"].format(util.pretty_float(total_val) + "%", util.pretty_float(threshold_val) + "%")
                    num_error.append({"node": "total", "value":symptom})
            trend.append(("variance", util.two_pass_variance(data)))
            if len(num_error) > 0:
                trend.append(("error", num_error))

            result[bucket] = trend
        if len(stats_buffer.buckets) > 0:
            result["cluster"] = {"value" : util.pretty_float(sum(cluster) / len(stats_buffer.buckets)) + "%",
                                 "raw" : cluster}
        return result

class MemUsed:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            total = 0
            data = []
            for node, vals in nodeStats.iteritems():
                if len(timestamps) > 0:
                    #avg = sum(vals) / samplesCount
                    a, b = util.linreg(timestamps, vals)
                    avg = a * timestamps[-1]  + b
                else:
                    avg = 0
                trend.append((node, {"value" : util.size_label(avg), "raw" : vals}))
                data.append(avg)
            if len(nodeStats) > 0:
                total_val = sum(data) / len(nodeStats)
                trend.append(("total", {"value" : util.size_label(total_val), "raw" : data}))
            trend.append(("variance", util.two_pass_variance(data)))
            result[bucket] = trend
        return result

class ItemGrowth:
    def run(self, accessor, scale, threshold=None):
        per_day = 86400000 #ms
        ratio = per_day
        result = {}
        cluster = []
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            trend = []
            total = []
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                a, b = util.linreg(timestamps, vals)
                rate = a * ratio
                total.append(rate)
                trend.append((node, {"value" : util.number_label(rate) + " items per day",
                                     "raw" : vals,
                                    }))
            if len(nodeStats) > 0:
                rate = sum(total) / len(nodeStats)
                trend.append(("total", {"value" : util.number_label(rate) + " items per day",
                                        "raw" : total}))
                cluster.append(rate)
            else:
                cluster.append(0.0)
            result[bucket] = trend
        if len(stats_buffer.buckets) > 0:
            rate = sum(cluster) / len(stats_buffer.buckets)
            result["cluster"] = {"value" : util.number_label(rate) + " items per day",
                                 "raw" : cluster}
        return result

class NumVbuckt:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if threshold.has_key("VBucketNumber"):
            threshold_val = threshold["VBucketNumber"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        num_node = len(stats_buffer.nodes)
        if num_node == 0:
            return result
        avg_threshold = threshold_val / num_node
        total_vbucket = 0
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            num_warn = []
            trend = []
            values = stats_info[scale][accessor["counter"]]
            nodeStats = values["nodeStats"]
            total = []
            for node, vals in nodeStats.iteritems():
                if len(vals) == 0:
                    numVal = 0
                else:
                    numVal = int(vals[-1])
                total_vbucket += numVal
                #if numVal > 0 and numVal < avg_threshold:
                #    symptom = accessor["symptom"].format(numVal, avg_threshold)
                #    num_warn.append({"node":node, "value": symptom})
                trend.append((node, {"value" : numVal,"raw" : vals,}))
                total.append(numVal)
            if len(nodeStats) > 0:
                trend.append(("total", {"value" : sum(total), "raw":total}))
            if len(num_warn) > 0:
                trend.append(("warn", num_warn))
            if total_vbucket < threshold_val:
                num_error = []
                symptom = accessor["symptom"].format(total_vbucket, threshold_val)
                num_error.append({"node": "total", "value": symptom})
                trend.append(("error", num_error))
            result[bucket] = trend
        return result

class VbucketMapSanity:
    def run(self, accessor, scale, threshold=None):
        result = {}

        for bucket, bucketinfo in stats_buffer.bucket_info.iteritems():
            if not bucketinfo.has_key('vBucketServerMap'):
                continue
            num_error = []
            trend = []
            numReplica = bucketinfo['vBucketServerMap']['numReplicas']
            vbucketMap = bucketinfo['vBucketServerMap']['vBucketMap']
            len_serverMap = len(bucketinfo['vBucketServerMap']['serverList'])
            # check one - vbucket map length
            len_map = len(vbucketMap)
            if len_map != accessor["threshold"]:
                symptom = "vBucketMap length {0} is not equal to {1}".format(len_map, accessor["threshold"])
                num_error.append({"node" : "total", "value" : symptom})

            correct_len = numReplica + 1
            for vbucket in vbucketMap:
                if type(vbucket) is list:
                    len_element = len(vbucket)
                    #check two - each vbucket map correctness
                    if len_element != correct_len:
                        symptom = "vBucketMap element length {0} is not consistent to replica {1}".format(len_element, numReplica)
                        num_error.append({"node" : "total", "value" : symptom})
                        trend.append((node, len_element))
                    for element in vbucket:
                        #check three - each vbucket index correctness
                        if element > len_serverMap - 1:
                            symptom = "vBucketMap element server index {0} can not be found in server list".format(element)
                            num_error.append({"node" : "total", "value" : symptom})
                            trend.append((node, element))
                    #check four - check unqiueness for vbucket
                    new_set = set(vbucket)
                    if len(new_set) < len_element:
                        symptom = "vBucketMap element {0} violates index uniqueness".format(vbucket)
                        num_error.append({"node" : "total", "value" : symptom})
                        trend.append((node, vbucket))
            if len(num_error) > 0:
                trend.append(("error", num_error))
            result[bucket] = trend

        return result


class VbucketServerListSanity:
    def run(self, accessor, scale, threshold=None):
        result = {}

        for bucket, bucketinfo in stats_buffer.bucket_info.iteritems():
            if not bucketinfo.has_key('vBucketServerMap'):
                continue
            num_error = []
            trend = []
            serverMap = bucketinfo['vBucketServerMap']['serverList']
            new_set = set(serverMap)
            if len(new_set) < len(serverMap):
                symptom = "vBucketMap server list {0} violates node uniqueness".format(serverMap)
                num_error.append({"node" : "total", "value" : symptom})
                trend.append((node, serverMap))
            if len(num_error) > 0:
                trend.append(("error", num_error))
            result[bucket] = trend

        return result

class RebalanceStuck:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if threshold.has_key("RebalancePerformance"):
            threshold_val = threshold["RebalancePerformance"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            num_warn = []
            res = []
            for node, stats_info in bucket_stats.iteritems():
                warnings = []
                for key, value in stats_info.iteritems():
                    if key.find(accessor["counter"]) >= 0:
                        if int(value) > threshold_val:
                            warnings.append(value)
                if len(warnings) > 0:
                    symptom = accessor["symptom"].format(len(warnings), threshold_val)
                    num_warn.append({"node":node, "value": symptom})
                    res.append((node, {"value":symptom, "raw":warnings}))
            if len(num_warn) > 0:
                res.append(("warn", num_warn))
            result[bucket] = res
        return result

class CalcFragmentation:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if threshold.has_key("MemoryFragmentation"):
            threshold_val = threshold["MemoryFragmentation"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            num_error = []
            trend = []
            for node, stats_info in bucket_stats.iteritems():
                for key, value in stats_info.iteritems():
                    if key == accessor["counter"]:
                        if accessor.has_key("threshold") and not isinstance(value, dict):
                            value = int(value)
                            if value > threshold_val:
                                symptom = ""
                                if accessor.has_key("unit"):
                                    if accessor["unit"] == "time":
                                        symptom = accessor["symptom"].format(util.time_label(value), util.time_label(threshold_val))
                                    elif accessor["unit"] == "size":
                                        symptom = accessor["symptom"].format(util.size_label(value), util.size_label(threshold_val))
                                    else:
                                        symptom = accessor["symptom"].format(value, threshold_val)
                                    num_error.append({"node":node, "value": symptom})
                                else:
                                    symptom = accessor["symptom"].format(value, threshold_val)
                                    num_error.append({"node":node, "value": symptom})
                        if accessor.has_key("unit"):
                            if accessor["unit"] == "time":
                                trend.append((node, {"value":util.time_label(value), "raw":value}))
                            elif accessor["unit"] == "size":
                                trend.append((node, {"value":util.size_label(value), "raw":value}))
                            else:
                                trend.append((node, value))
            if len(num_error) > 0:
                trend.append(("error", num_error))
                result[bucket] = trend
        return result

class EPEnginePerformance:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if threshold.has_key("EPEnginePerformance"):
            threshold_val = threshold["EPEnginePerformance"][accessor["name"]]
        else:
            threshold_val = accessor["threshold"]
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            num_error = []
            for node, stats_info in bucket_stats.iteritems():
                for key, value in stats_info.iteritems():
                    if key.find(accessor["counter"]) >= 0:
                        if accessor.has_key("threshold"):
                            if accessor["counter"] == "flusherState" and value != threshold_val:
                                num_error.append({"node":node, "value": accessor["symptom"]})
                            elif accessor["counter"] == "flusherCompleted" and value == threshold_val:
                                num_error.append({"node":node, "value": accessor["symptom"]})
                            else:
                                if value > threshold_val:
                                    if accessor.has_key("unit"):
                                        if accessor["unit"] == "time":
                                            symptom = accessor["symptom"].format(util.time_label(int(value)), util.time_label(threshold_val))
                                        elif accessor["unit"] == "size":
                                            symptom = accessor["symptom"].format(util.size_label(int(value)), util.size_label(threshold_val))
                                        else:
                                            symptom = accessor["symptom"].format(value, threshold_val)
                                    else:
                                        symptom = accessor["symptom"].format(value, threshold_val)
                                    num_error.append({"node":node, "value": symptom})
            if len(num_error) > 0:
                result[bucket] = {"error" : num_error}
        return result

class TotalDataSize:
    def run(self, accessor, scale, threshold=None):
        total = 0
        for node, nodeinfo in stats_buffer.nodes.iteritems():
            if nodeinfo["status"] != "healthy":
                continue
            if nodeinfo["StorageInfo"].has_key("hdd"):
                total += nodeinfo['StorageInfo']['hdd']['usedByData']
        return util.size_label(total)

class AvailableDiskSpace:
    def run(self, accessor, scale, threshold=None):
        result = {}
        total = 0
        space = []
        for node, nodeinfo in stats_buffer.nodes.iteritems():
            if nodeinfo["status"] != "healthy":
                continue
            if nodeinfo["StorageInfo"].has_key("hdd"):
                total += nodeinfo['StorageInfo']['hdd']['free']
                space.append(nodeinfo['StorageInfo']['hdd']['free'])
        result["cluster"] = {"value" :util.size_label(total), "raw":space}
        return result

class LeastDiskSpace:
    def run(self, accessor, scale, threshold=None):
        result = {}
        least = { "node":None, "space":0 }
        space = []
        for node, nodeinfo in stats_buffer.nodes.iteritems():
            if nodeinfo["status"] != "healthy":
                continue
            if nodeinfo["StorageInfo"].has_key("hdd"):
                if least["space"] == 0 or least["space"] >  nodeinfo['StorageInfo']['hdd']['free']:
                    least["node"] = node
                    least["space"] = nodeinfo['StorageInfo']['hdd']['free']
                space.append((node, nodeinfo['StorageInfo']['hdd']['free']))
        symptom = accessor["symptom"].format(least["node"], util.size_label(least["space"]))
        result["cluster"] = {"value" :symptom, "raw" : space}
        return result

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
            "formula" : "Storage['hdd']['free']",
        },
        {
            "name" : "minFreeDiskSpace",
            "description" : "Node with least available disk space",
            "code" : "LeastDiskSpace",
            "symptom" : "'{0}' with space '{1}'",
            "formula" : "Min(Storage['hdd']['free'])",
        },
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
            "symptom" : "Cache miss ratio '{0}%' is higher than threshold '{1}%'",
            "counter" : "ep_cache_miss_rate",
            "scale" : "hour",
            "code" : "CacheMissRatio",
            "threshold" : 2,
            "formula" : "Avg(ep_cache_miss_rate)",
        },
     ],
     "clusterwise" : True,
     "perNode" : True,
     "perBucket" : True,
     "indicator" : True,
     "nodeDisparate" : True,
    },
    {"name" : "DGM",
     "ingredients" : [
        {
            "name" : "dgm",
            "description" : "Disk to memory ratio",
            "code" : "DGMRatio",
            "formula" : "Total(Storage['hdd']['usedByData']) / Total(Storage['ram']['usedByData'])",
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
            "threshold" : 5,
            "symptom" : "Active to replica resident ratio difference'{0}%' is bigger than '{1}%'",
            "formula" : "Avg(curr_items) / Avg(vb_replica_curr_items)",
        },
        {
            "name" : "activeResidentRatio",
            "description" : "Active resident ratio",
            "counter" : "vb_active_resident_items_ratio",
            "scale" : "minute",
            "code" : "ResidentItemRatio",
            "threshold" : 30,
            "symptom" : "Active resident item ratio '{0}' is less than '{1}'",
            "formula" : "Last(vb_active_resident_items_ratio)",
        },
        {
            "name" : "replicaResidentRatio",
            "description" : "Replica resident ratio",
            "counter" : "vb_replica_resident_items_ratio",
            "scale" : "minute",
            "code" : "ResidentItemRatio",
            "threshold" : 20,
            "symptom" : "Replica resident item ratio '{0}' is less than '{1}'",
            "formula" : "Last(vb_replica_resident_items_ratio)",
        },
     ],
     "clusterwise" : True,
     "perNode" : True,
     "perBucket" : True,
     "indicator" : True,
    },
    {"name" : "OPSPerformance",
     "ingredients" : [
        {
            "name" : "opsPerformance",
            "description" : "Read/Write/Delete ops ratio",
            "scale" : "week",
            "counter" : ["cmd_get", "cmd_set", "delete_hits"],
            "code" : "OpsRatio",
            "formula" : "Avg(cmd_get) : Avg(cmd_get) : Avg(delete_hits)",
        },
     ],
     "perBucket" : True,
     "clusterwise" : True,
    },
    {"name" : "GrowthRate",
     "ingredients" : [
        {
            "name" : "dataGrowthRateForItems",
            "description" : "Average data growth rate for items",
            "counter" : "curr_items",
            "scale" : "day",
            "code" : "ItemGrowth",
            "formula" : "Linear(curr_items)",
        },
     ],
     "clusterwise" : True,
     "perBucket" : True,
     "perNode" : True,
    },
    {"name" : "VBucketNumber",
     "ingredients" : [
        {
            "name" : "activeVbucketNumber",
            "description" : "Active VBucket number",
            "counter" : "vb_active_num",
            "scale" : "hour",
            "code" : "NumVbuckt",
            "threshold" : 1024,
            "symptom" : "Number of active vBuckets '{0}' is less than '{1}' per node",
            "formula" : "Avg(vb_active_num)",
        },
        {
            "name" : "replicaVBucketNumber",
            "description" : "Replica VBucket number",
            "counter" : "vb_replica_num",
            "scale" : "hour",
            "code" : "NumVbuckt",
            "threshold" : 1024,
            "symptom" : "Number of replica vBuckets '{0}' is less than '{1}' per node", 
            "formula" : "Avg(vb_replica_num)",
        },
     ],
     "indicator" : True,
     "perBucket" : True,
     "perNode" : True,
    },
    {"name" : "VBucketServerMap",
     "ingredients" : [
        {
            "name" : "vbucketMap",
            "description" : "Sanity checks for vBucket map",
            "code" : "VbucketMapSanity",
            "threshold" : 1024,
            "formula" : "",
        },
        {
            "name" : "vbucketServerList",
            "description" : "Sanity checks for vBucket server list",
            "code" : "VbucketServerListSanity",
            "formula" : "",
        },
     ],
     "indicator" : True,
     "perBucket" : True,
    },
    {"name" : "MemoryUsage",
     "ingredients" : [
        {
            "name" : "memoryUsage",
            "description" : "Memory usage",
            "counter" : "mem_used",
            "scale" : "hour",
            "code" : "MemUsed",
            "formula" : "Avg(mem_used)",
        },
     ],
     "perNode" : True,
     "perBucket" : True,
     "nodeDisparate" : True,
    },
    {"name" : "RebalancePerformance",
     "ingredients" : [
        {
            "name" : "highBackfillRemaing",
            "description" : "Tap queue backfill remaining is too high",
            "counter" : "ep_tap_queue_backfillremaining",
            "code" : "RebalanceStuck",
            "threshold" : 1000,
            "symptom" : "There are {0} stats showing tap queue backfill remainings higher than threshold '{1}'",
            "formula" : "Total(ep_tap_queue_backfillremaining > threshold)",
        },
        {
            "name" : "tapNack",
            "description" : "Number of Tap stream backoff",
            "counter" : "num_tap_nack",
            "code" : "RebalanceStuck",
            "threshold" : 5,
            "symptom" : "Backoff received above threshold '{1}'",
            "formula" : "Total(num_tap_nack > threshold)",
        },
     ],
     "indicator" : True,
     "perBucket" : True,
    },
    {"name" : "MemoryFragmentation",
     "ingredients" : [
        {
            "name" : "totalFragmentation",
            "description" : "Total memory fragmentation",
            "counter" : "total_fragmentation_bytes",
            "code" : "CalcFragmentation",
            "unit" : "size",
            "threshold" : 1073741824,  # 1GB
            "symptom" : "Total memory fragmentation '{0}' is larger than '{1}'",
            "formula" : "total_fragmentation_bytes > threshold",
        },
      ],
      "indicator" : True,
    },
    {"name" : "DiskFragmentation",
     "ingredients" : [
        {
            "name" : "diskDelete",
            "description" : "Average disk delete time",
            "counter" : "disk_del",
            "code" : "CalcFragmentation",
            "unit" : "time",
            "threshold" : 1000,     #1ms
            "symptom" : "Average disk delete time '{0}' is slower than '{1}'",
            "formula" : "Avg(disk_del) > threshold",
        },
        {
            "name" : "diskUpdate",
            "description" : "Average disk update time",
            "counter" : "disk_update",
            "code" : "CalcFragmentation",
            "unit" : "time",
            "threshold" : 1000,     #1ms
            "symptom" : "Average disk update time '{0}' is slower than '{1}'",
            "formula" : "Avg(disk_update) > threshold",
        },
        {
            "name" : "diskInsert",
            "description" : "Average disk insert time",
            "type" : "python",
            "counter" : "disk_insert",
            "code" : "CalcFragmentation",
            "unit" : "time",
            "threshold" : 1000,     #1ms
            "symptom" : "Average disk insert time '{0}' is slower than '{1}'",
            "formula" : "Avg(disk_insert) > threshold",
        },
        {
            "name" : "diskCommit",
            "description" : "Average disk commit time",
            "counter" : "disk_commit",
            "code" : "CalcFragmentation",
            "unit" : "time",
            "threshold" : 5000000,     #10s
            "symptom" : "Average disk commit time '{0}' is slower than '{1}'",
            "formula" : "Avg(disk_commit) > threshold",
        },
     ],
     "indicator" : True,
     "perBucket" : True,
    },
    {"name" : "EPEnginePerformance",
     "ingredients" : [
        {
            "name" : "flusherState",
            "description" : "Engine flusher state",
            "counter" : "ep_flusher_state",
            "code" : "EPEnginePerformance",
            "threshold" : "running",
            "symptom" : "The flusher is not running",
            "formula" : "ep_flusher_state == True",
        },
        {
            "name" : "flusherCompleted",
            "description" : "Flusher completed",
            "counter" : "ep_flusher_num_completed",
            "code" : "EPEnginePerformance",
            "threshold" : 0,
            "symptom" : "The flusher is not persisting any items",
            "formula" : "ep_flusher_num_completed == 0",
        },
        {
            "name" : "avgItemLoadTime",
            "description" : "Average item loaded time",
            "counter" : "ep_bg_load_avg",
            "code" : "EPEnginePerformance",
            "unit" : "time",
            "threshold" : 100,
            "symptom" : "Average time '{0}' for items to be loaded is slower than '{1}'",  
            "formula" : "Avg(ep_bg_load_avg) > threshold",
        },
        {
            "name" : "avgItemWaitTime",
            "description" : "Average item waited time",
            "counter" : "ep_bg_wait_avg",
            "code" : "EPEnginePerformance",
            "unit" : "time",
            "threshold" : 100,
            "symptom" : "Average wait time '{0}' for items to be serviced by dispatcher is slower than '{1}'",
            "formula" : "Avg(ep_bg_wait_avg) > threshold",
        },
     ],
     "indicator" : True,
    },
]
