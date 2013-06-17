
import stats_buffer
import util_cli as util

class NodeList:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for node, node_info in stats_buffer.nodes.iteritems():
            if node_info['status'] == "healthy":
                result[node] = {"host" : node_info['host'], "ip": node, "port": node_info['port'], "version" :node_info['version'], "os": node_info['os'], "status" :node_info['status']}
            else:
                result[node] = {"host" : node_info['host'], "ip": node, "port": node_info['port'], "version" :"N/A", "os": "N/A", "status" :node_info['status']}
        return result

class NumNodes:
    def run(self, accessor, scale, threshold=None):
        return {"total": len(stats_buffer.nodes)}

class NumDownNodes:
    def run(self, accessor, scale, threshold=None):
        return {"total": len(filter(lambda (a, b): b["status"]=="down" or b["status"]=="unhealthy", stats_buffer.nodes.items()))}

class NumWarmupNodes:
    def run(self, accessor, scale, threshold=None):
        return {"total": len(filter(lambda (a, b): b["status"]=="warmup", stats_buffer.nodes.items()))}

class NumFailOverNodes:
    def run(self, accessor, scale, threshold=None):
        return {"total": len(filter(lambda (a, b): b.has_key("clusterMembership") and b["clusterMembership"]!="active", stats_buffer.nodes.items()))}

class NodeSizing:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for node, values in stats_buffer.nodes.iteritems():
            if values["status"] != "healthy":
                continue
            if isinstance(accessor["counter"], list):
                val = values[accessor["category"]][accessor["counter"][0]] - values[accessor["category"]][accessor["counter"][1]]
            else:
                if accessor.has_key("suffix"):
                    val = values[accessor["category"]][accessor["counter"]][accessor["suffix"]]
                else:
                    val = values[accessor["category"]][accessor["counter"]]
        result[node] = val
        if accessor.has_key("unit"):
            if accessor["unit"] == "size":
                result[node] = util.size_label(val)
        return result

class NodeSizingNone:
    def run(self, accessor, scale, threshold=None):
        result = {}
        return result

class NodeSizingCacheMissRatio:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                trend = 0
                if len(vals):
                    trend, b = util.linreg(timestamps, vals)
                if result.has_key(node):
                    result[node].append((bucket, trend))
                else:
                    result[node] = [(bucket, trend)]
        return result

class BucketList:
    def run(self, accessor, scale, threshold=None):
        result = []
        for bucket, bucketinfo in stats_buffer.bucket_info.iteritems():
            result.append({"name": bucket, "type": bucketinfo["bucketType"]})

        return result

class NodeStorageStats:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for node, values in stats_buffer.nodes.iteritems():
            if values["status"] != "healthy":
                continue
            if values["StorageInfo"].has_key("hdd"):
                result[node] = {
                           "ip": values["host"],
                           "port": values["port"],
                           "type" : "hdd",
                           "free": util.size_label(values["StorageInfo"]["hdd"]["free"]),
                           "quotaTotal" : util.size_label(values["StorageInfo"]["hdd"]["quotaTotal"]),
                           "used" : util.size_label(values["StorageInfo"]["hdd"]["used"]),
                           "usedByData" : util.size_label(values["StorageInfo"]["hdd"]["usedByData"]),
                           "total" : util.size_label(values["StorageInfo"]["hdd"]["total"])}
            if values["StorageInfo"].has_key("ram"):
                result[node] = {
                           "ip": values["host"],
                           "port": values["port"],
                           "type" : "ram",
                           "quotaTotal" : util.size_label(values["StorageInfo"]["ram"]["quotaTotal"]),
                           "used" : util.size_label(values["StorageInfo"]["ram"]["used"]),
                           "usedByData" : util.size_label(values["StorageInfo"]["ram"]["usedByData"]),
                           "total" : util.size_label(values["StorageInfo"]["ram"]["total"])}
        return result

class NodeSystemStats:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for node, values in stats_buffer.nodes.iteritems():
            if values["status"] != "healthy":
                continue
            result[node] = {
                    "ip": values["host"],
                    "port": values["port"],
                    "cpuUtilization" :util.pretty_float(values["systemStats"]["cpu_utilization_rate"]),
                    "swapTotal": util.size_label(values["systemStats"]["swap_total"]),
                    "swapUsed" : util.size_label(values["systemStats"]["swap_used"]),
                    "currentItems" : values["systemStats"]["currentItems"],
                    "currentItemsTotal" : values["systemStats"]["currentItemsTotal"],
                    "replicaCurrentItems" : values["systemStats"]["replicaCurrentItems"]}

        return result

class ConnectionTrend:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            for node, vals in nodeStats.iteritems():
                if len(vals) == 0:
                    trend.append((node, 0, 0))
                else:
                    a, b = util.linreg(timestamps, vals)
                    trend.append((node, a, vals[-1]))
            result[bucket] = trend
        return result

class CalcTrend:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            trend = []
            for node, vals in nodeStats.iteritems():
                if samplesCount > 0:
                    avg = sum(vals) / samplesCount
                else:
                    avg = 0
                trend.append((node, util.pretty_float(avg)))
            result[bucket] = trend
        return result

class NodePerformanceStats:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if threshold.has_key(accessor["name"]):
            threshold_val = threshold[accessor["name"]]
        elif accessor.has_key("threshold"):
            threshold_val = accessor["threshold"]
        else:
            threshold_val = None
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            stats = []
            for node, stats_info in bucket_stats.iteritems():
                if accessor["counter"] not in stats_info.keys():
                    stats.append((node, "N/A"))
                    continue
                for key, value in stats_info.iteritems():
                    if isinstance(value, dict):
                        continue
                    if key.find(accessor["counter"]) >= 0:
                        if accessor.has_key("threshold"):
                            if int(value) > threshold_val:
                                stats.append((node, (key, value)))
                        else:
                            if accessor.has_key("unit"):
                                if accessor["unit"] == "time":
                                    stats.append((node, util.time_label(value)))
                                elif accessor["unit"] == "size":
                                    stats.append((node, util.size_label(int(value))))
                            else:
                                stats.append((node, (key,value)))
            result[bucket] = stats
        return result

class AvgDocSize:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if threshold.has_key(accessor["name"]):
            threshold_val = threshold[accessor["name"]]
        elif accessor.has_key("threshold"):
            threshold_val = accessor["threshold"]
        else:
            threshold_val = None
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            stats = []
            for node, stats_info in bucket_stats.iteritems():
                if accessor["counter"][0] not in stats_info.keys():
                    stats.append((node, "N/A"))
                    continue
                for key, value in stats_info.iteritems():
                    if isinstance(value, dict):
                        continue
                    if key.find(accessor["counter"][0]) >= 0:
                        if accessor["counter"][1] in stats_info and \
                            accessor["counter"][2] in stats_info:
                            total_item_resident = int(stats_info[accessor["counter"][1]]) -\
                                                  int(stats_info[accessor["counter"][2]])
                            if total_item_resident:
                                value = float(value) / total_item_resident
                            else:
                                value = 0

                        if accessor.has_key("unit"):
                            if accessor["unit"] == "time":
                                stats.append((node, util.time_label(value)))
                            elif accessor["unit"] == "size":
                                stats.append((node, util.size_label(int(value))))
                        else:
                            stats.append((node, (key,value)))
            result[bucket] = stats
        return result

NodeCapsule = [
    {"name" : "NodeStatus",
     "ingredients" : [
        {
            "name" : "nodeList",
            "description" : "Node list",
            "code" : "NodeList",
        },
      ],
      "nodewise" : True,
    },
    {"name" : "NodeStatus",
     "ingredients" : [
        {
            "name" : "numNodes",
            "description" : "Number of nodes",
            "code" : "NumNodes",
        },
        {
            "name" : "numDownNodes",
            "description" : "Number of down nodes",
            "code" : "NumDownNodes",
        },
        {
            "name" : "numWarmupNodes",
            "description" : "Number of warmup nodes",
            "code" : "NumWarmupNodes",
        },
        {
            "name" : "numFailedOverNodes",
            "description" : "Number of nodes failed over",
            "code" : "NumFailOverNodes",
        },
      ],
      "clusterwise" : False,
      "nodewise" : False,
      "perNode" : False,
      "perBucket" : False,
    },
    {"name": "NodeSizing",
     "ingredients": [
        {
            "name": "availableMemory",
            "description": "Available Memory (RAM)",
            "code": "NodeSizing",
            "category": "memory",
            "counter": "free",
            "unit" : "size",
        },
        {
            "name": "availableDisk",
            "description": "Available Disk space",
            "code": "NodeSizing",
            "category": "StorageInfo",
            "counter": "hdd",
            "suffix": "free",
            "unit" : "size",
        },
        {
            "name": "availableSwap",
            "description": "Available Swap space",
            "code": "NodeSizing",
            "category": "systemStats",
            "counter": ["swap_total", "swap_used"],
            "unit" : "size",
        },
        {
            "name": "currSwap",
            "description": "Current usage of Swap space",
            "code": "NodeSizing",
            "category": "systemStats",
            "counter": "swap_used",
            "unit" : "size",
        },
        {
            "name": "currMemory",
            "description": "Current usage of Memory (RAM)",
            "code": "NodeSizing",
            "category": "memory",
            "counter": ["total", "free"],
            "unit" : "size",
        },
        {
            "name": "currDisk",
            "description": "Current usage of Disk space",
            "code": "NodeSizing",
            "category": "StorageInfo",
            "counter": "hdd",
            "suffix": "used",
            "unit" : "size",
        },
        {
            "name": "cpuUsage",
            "description": "Current usage of CPU",
            "code": "NodeSizing",
            "category": "systemStats",
            "counter": "cpu_utilization_rate",
        },
        {
            "name": "volumes",
            "description": "List of Volumes",
            "code": "NodeSizingNone",
            "category": "systemStats",
            "counter": "cpu_utilization_rate",
        },
        {
            "name": "dataGrowth",
            "description": "Data growth trend",
            "code": "NodeSizingNone",
            "category": "systemStats",
            "counter": "cpu_utilization_rate",
        },
        {
            "name": "memoryGrowth",
            "description": "Amount of memory growth trend",
            "code": "NodeSizingNone",
            "category": "systemStats",
            "counter": "cpu_utilization_rate",
        },
        {
            "name": "cacheMissRatio",
            "description": "Cachemiss ratio growth",
            "code": "NodeSizingCacheMissRatio",
            "counter": "ep_cache_miss_rate",
        },
     ],
     "sizing": True,
    },
    {"name" : "NumberOfConnection",
    "ingredients" : [
        {
            "name" : "connectionTrend",
            "description" : "Connection trend",
            "counter" : "curr_connections",
            "scale" : "minute",
            "code" : "ConnectionTrend",
            "threshold" : {
                "high" : 1000,
            },
            "symptom" : "Number of connections '%s' reaches connection maximum '%s'",
            "formula" : "Avg(curr_connections) > threshold",
        },
     ],
     "nodewise" : False,
     "perNode" : True,
    },
    {"name" : "OOMError",
     "ingredients" : [
        {
            "name" : "oomErrors",
            "description" : "OOM errors",
            "counter" : "ep_oom_errors",
            "scale" : "hour",
            "code" : "CalcTrend",
            "formula" : "ep_oom_errors",
        },
        {
            "name" : "tempOomErrors",
            "description" : "Temporary OOM errors",
            "counter" : "ep_tmp_oom_errors",
            "scale" : "hour",
            "code" : "CalcTrend",
            "formula" : "ep_tmp_oom_errors",
        },
     ],
     "nodewise" : False,
     "perBucket"  : False,
    },
    {"name" : "nodeStorageStats",
     "ingredients" : [
        {
            "name" : "nodeStorageStats",
            "description" : "Node storage stats",
            "code" : "NodeStorageStats",
        },
     ],
     "sizing" : False,
    },
    {"name" : "nodeSystemStats",
     "ingredients" : [
        {
            "name" : "nodeSystemStats",
            "description" : "Node system stats",
            "code" : "NodeSystemStats",
        },
     ],
     "sizing" : False,
    },
    {"name" : "checkpointPerformance",
     "ingredients" : [
        {
            "name" : "openCheckPoint",
            "description" : "Items for open checkpoints",
            "counter" : "num_checkpoint_items",
            "code" : "NodePerformanceStats",
            "threshold" : 1000,
            "symptom" : "Number of items in a checkpoint '%s' reaches threshold '%s'",
            "formula" : "num_checkpoint_items > threshold",
        },
     ],
     "perBucket" : False,
    },
    {"name" : "AverageDocumentSize",
     "ingredients" : [
        {
            "name" : "averageDocumentSize",
            "description" : "Average document size",
            "counter" : ["ep_value_size", "curr_items_tot", "ep_num_non_resident"],
            "code" : "AvgDocSize",
            "unit" : "size",
            "formula" : "ep_kv_size",
        },
     ],
     "perBucket" : True,
    },
    {"name" : "MemoryUsage",
     "ingredients" : [
        {
            "name" : "totalMemoryUsage",
            "description" : "Total memory usage",
            "counter" : "total_heap_bytes",
            "code" : "NodePerformanceStats",
            "unit" : "size",
            "formula" : "total_heap_bytes",
        },
        {
            "name" : "totalInternalMemory",
            "description" : "Total internal memory usage",
            "counter" : "mem_used",
            "code" : "NodePerformanceStats",
            "unit" : "size",
            "formula" : "mem_used",
        },
        {
            "name" : "overhead",
            "description" : "Memory overhead",
            "counter" : "ep_overhead",
            "scale" : "hour",
            "code" : "NodePerformanceStats",
            "unit" : "size",
            "formula" : "ep_overhead",
        },
     ],
     "perBucket" : True,
    },
    {"name" : "EPEnginePerformance",
     "ingredients" : [
        {
            "name" : "flusherState",
            "description" : "Engine flusher state",
            "counter" : "ep_flusher_state",
            "code" : "NodePerformanceStats",
            "formula" : "ep_flusher_state",
        },
        {
            "name" : "flusherCompleted",
            "description" : "Flusher completed",
            "counter" : "ep_flusher_num_completed",
            "code" : "NodePerformanceStats",
            "formula" : "ep_flusher_num_completed",
        },
        {
            "name" : "avgItemLoadTime",
            "description" : "Average item loaded time",
            "counter" : "ep_bg_load_avg",
            "code" : "NodePerformanceStats",
            "unit" : "time",
            "formula" : "ep_bg_load_avg",
        },
        {
            "name" : "avgItemWaitTime",
            "description" : "Average item waited time",
            "counter" : "ep_bg_wait_avg",
            "code" : "NodePerformanceStats",
            "unit" : "time",
            "formula" : "ep_bg_wait_avg",
        },
     ],
     "perNode" : True,
    },
]


