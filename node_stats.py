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
            val = None
            if isinstance(accessor["counter"], list):
                val = values[accessor["countergroup"]][accessor["counter"][0]] - values[accessor["countergroup"]][accessor["counter"][1]]
            else:
                if accessor.has_key("suffix"):
                    val = values[accessor["countergroup"]][accessor["counter"]][accessor["suffix"]]
                else:
                    val = values[accessor["countergroup"]][accessor["counter"]]
            if val:
                result[node] = val
                if accessor.has_key("unit"):
                    if accessor["unit"] == "size":
                        result[node] = util.size_label(val)
        return result

class DiskInfo:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for node, values in stats_buffer.nodes.iteritems():
            if values["status"] != "healthy":
                continue
            result[node] = []
            for key, val in values["availableStorage"].iteritems():
                result[node].append((key, val))
        return result

class DiskSizing:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for node, values in stats_buffer.nodes.iteritems():
            if values["status"] != "healthy":
                continue
            result[node] = []
            for val in values["StorageInfo"]["storage"]:
                result[node].append((values['StorageInfo']['type'], val[accessor["counter"]]))
        return result

class NodeSizingNone:
    def run(self, accessor, scale, threshold=None):
        result = {}
        return result

class TrendSizing:
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

class AverageSizing:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            for node, vals in nodeStats.iteritems():
                if len(vals):
                    avg = sum(vals) / len(vals)
                else:
                    avg = 0
                if result.has_key(node):
                    result[node].append((bucket, util.pretty_float(avg)))
                else:
                    result[node] = [(bucket, util.pretty_float(avg))]
        return result

class LatestSizing:
    def run(self, accessor, scale, threshold=None):
        result = {}
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[scale][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            for node, vals in nodeStats.iteritems():
                if len(vals):
                    avg = vals[-1]
                else:
                    avg = 0
                if accessor.has_key("unit"):
                    if accessor["unit"] == "size":
                        avg = util.size_label(avg)
                    elif accessor["unit"] == "number":
                        avg = util.number_label(avg)
                    elif accessor["unit"] == "time":
                        avg = util.time_label(avg)
                    else:
                        avg = util.pretty_float(avg)
                if result.has_key(node):
                    result[node].append((bucket, avg))
                else:
                    result[node] = [(bucket, avg)]
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
        sizing = {}
        if threshold.has_key(accessor["name"]):
            threshold_val = threshold[accessor["name"]]
        elif accessor.has_key("threshold"):
            threshold_val = accessor["threshold"]
        else:
            threshold_val = None
        for bucket, bucket_stats in stats_buffer.node_stats.iteritems():
            stats = []
            for node, stats_info in bucket_stats.iteritems():
                if not sizing.has_key(node):
                    sizing[node] = []
                if accessor["counter"][0] not in stats_info.keys():
                    stats.append((node, "N/A"))
                    sizing[node].append((bucket, "N/A"))
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
                                sizing[node].append((bucket, util.time_label(value)))
                            elif accessor["unit"] == "size":
                                stats.append((node, util.size_label(int(value))))
                                sizing[node].append((bucket, util.size_label(int(value))))
                        else:
                            stats.append((node, (key,value)))
            result[bucket] = stats
        result["_sizing"] = sizing
        return result

class GrowthChartData:
    def run(self, accessor, scale, threshold=None):
        result = {}
        if scale != accessor["scale"]:
            return result
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            if not stats_info[scale].has_key(accessor["counter"]):
                continue
            values = stats_info[scale][accessor["counter"]]
            if values is None:
                continue
            timestamps = values["timestamp"]
            nodeStats = values["nodeStats"]
            trend = []
            for node, vals in nodeStats.iteritems():
                samplesCount = len(vals)
                start = int(samplesCount * accessor["period"])
                for t,v in zip(timestamps[-start:], vals[-start:]):
                    t = str(t)
                    if accessor.has_key("unit"):
                        trend.append(list((t,util.size_convert(v, accessor["unit"]))))
                    else:
                        trend.append(list((t, str(v))))

                if result.has_key(node):
                    result[node].append((bucket, trend))
                else:
                    result[node] = [(bucket, trend)]

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
            "countergroup": "memory",
            "counter": "free",
            "unit": "size",
            "category": "Memory",
        },
        {
            "name": "availableDisk",
            "description": "Available Disk space",
            "code": "NodeSizing",
            "countergroup": "StorageInfo",
            "counter": "hdd",
            "suffix": "free",
            "unit" : "size",
            "category": "Disk",
        },
        {
            "name": "availableSwap",
            "description": "Available Swap space",
            "code": "NodeSizing",
            "countergroup": "systemStats",
            "counter": ["swap_total", "swap_used"],
            "unit" : "size",
            "category": "Memory",
        },
        {
            "name": "currSwap",
            "description": "Current usage of Swap space",
            "code": "NodeSizing",
            "countergroup": "systemStats",
            "counter": "swap_used",
            "unit" : "size",
            "category": "Memory",
        },
        {
            "name": "currMemory",
            "description": "Current usage of Memory (RAM)",
            "code": "NodeSizing",
            "countergroup": "memory",
            "counter": ["total", "free"],
            "unit" : "size",
            "category": "Memory",
        },
        {
            "name": "currDisk",
            "description": "Current usage of Disk space",
            "code": "NodeSizing",
            "countergroup": "StorageInfo",
            "counter": "hdd",
            "suffix": "used",
            "unit" : "size",
            "category": "Disk",
        },
        {
            "name": "cpuUsage",
            "description": "Current usage of CPU",
            "code": "NodeSizing",
            "countergroup": "systemStats",
            "counter": "cpu_utilization_rate",
            "category": "CPU",
        },
        {
            "name": "volumes",
            "description": "List of Volumes",
            "code": "NodeSizingNone",
            "countergroup": "systemStats",
            "counter": "cpu_utilization_rate",
            "category": "CPU",
        },
        {
            "name": "dataGrowth",
            "description": "Data growth trend",
            "code": "NodeSizingNone",
            "countergroup": "systemStats",
            "counter": "cpu_utilization_rate",
            "category": "CPU",
        },
        {
            "name": "memoryGrowth",
            "description": "Amount of memory growth trend",
            "code": "NodeSizingNone",
            "countergroup": "systemStats",
            "counter": "cpu_utilization_rate",
            "category": "Memory",
        },
        {
            "name": "cacheMissRatio",
            "description": "Cachemiss ratio growth",
            "code": "TrendSizing",
            "counter": "ep_cache_miss_rate",
            "category": "Memory",
        },
        {
            "name": "diskWriteQueueLength",
            "description": "Average Disk write queue length",
            "code": "AverageSizing",
            "counter": "disk_write_queue",
            "category": "Disk IO",
        },
        {
            "name": "dataDiskSize",
            "description": "Current document size on disk",
            "code": "LatestSizing",
            "counter": "couch_docs_actual_disk_size",
            "category": "Disk IO",
            "unit": "size"
        },
        {
            "name": "diskCommitTime",
            "description": "Disk commit time",
            "code": "LatestSizing",
            "counter": "avg_disk_commit_time",
            "category": "Disk IO",
            "unit": "time"
        },
        {
            "name": "numItem",
            "description": "Current number of active items",
            "code": "LatestSizing",
            "counter": "curr_items",
            "category": "Disk",
            "unit": "number",
        },
        {
            "name": "viewDiskSize",
            "description": "Current index size on disk",
            "code": "LatestSizing",
            "counter": "couch_views_actual_disk_size",
            "category": "Disk IO",
            "unit": "size",
        },
        {
            "name": "dataPath",
            "description": "Data path on disk",
            "code": "DiskSizing",
            "counter": "path",
            "category": "Disk",
        },
        {
            "name": "indexPath",
            "description": "Index data path on disk",
            "code": "DiskSizing",
            "counter": "index_path",
            "category": "Disk",
        },
        {
            "name": "volumeInfo",
            "description": "Available volumes",
            "code": "DiskInfo",
            "category": "Disk",
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
            "category": "Disk IO",
            "formula" : "ep_kv_size",
        },
     ],
     "perBucket" : True,
     "sizing": True,
    },
    {"name" : "memoryGrowth",
     "ingredients" : [
        {
            "name" : "oneHourMemoryGrowth",
            "description" : "one hour memory usage growth",
            "counter" : "mem_used",
            "code" : "GrowthChartData",
            "period": 1.0,
            "scale": "hour",
            "unit" : "MB",
            "category": "Memory",
            "chart" : True,
        },
        {
            "name" : "oneDayMemoryGrowth",
            "description" : "one day memory usage growth",
            "counter" : "mem_used",
            "code" : "GrowthChartData",
            "period": 1.0,
            "scale": "day",
            "unit" : "MB",
            "category": "Memory",
            "chart" : True,
        },
        {
            "name" : "oneWeekMemoryGrowth",
            "description" : "one day memory usage growth",
            "counter" : "mem_used",
            "code" : "GrowthChartData",
            "period": 1.0,
            "scale": "week",
            "unit" : "MB",
            "category": "Memory",
            "chart" : True,
        },
        {
            "name" : "oneMonthMemoryGrowth",
            "description" : "one day memory usage growth",
            "counter" : "mem_used",
            "code" : "GrowthChartData",
            "period": 1.0,
            "scale": "month",
            "unit" : "MB",
            "category": "Memory",
            "chart" : True,
        },
        {
            "name" : "threeMonthMemoryGrowth",
            "description" : "3 month memory usage growth",
            "counter" : "mem_used",
            "code" : "GrowthChartData",
            "period": .25,
            "scale": "year",
            "unit" : "MB",
            "category": "Memory",
            "chart" : True,
        },
        {
            "name" : "sixMonthMemoryGrowth",
            "description" : "6 month memory usage growth",
            "counter" : "mem_used",
            "code" : "GrowthChartData",
            "period": .5,
            "scale": "year",
            "unit" : "MB",
            "category": "Memory",
            "chart" : True,
        },
        {
            "name" : "nineMonthMemoryGrowth",
            "description" : "9 month memory usage growth",
            "counter" : "mem_used",
            "code" : "GrowthChartData",
            "period": .75,
            "scale": "year",
            "unit" : "MB",
            "category": "Memory",
            "chart" : True,
        },
     ],
     "sizing": True,
    },
    {"name" : "diskSizeGrowth",
     "ingredients" : [
        {
            "name" : "oneHourDiskSizeGrowth",
            "description" : "one hour disk size usage growth",
            "counter" : "couch_total_disk_size",
            "code" : "GrowthChartData",
            "period": 1.0,
            "scale": "hour",
            "unit" : "MB",
            "category": "Disk",
            "chart" : True,
        },
        {
            "name" : "oneDayDiskSizeGrowth",
            "description" : "one day disk size usage growth",
            "counter" : "couch_total_disk_size",
            "code" : "GrowthChartData",
            "period": 1.0,
            "scale": "day",
            "unit" : "MB",
            "category": "Disk",
            "chart" : True,
        },
        {
            "name" : "oneWeekDiskSizeGrowth",
            "description" : "one week disk size usage growth",
            "counter" : "couch_total_disk_size",
            "code" : "GrowthChartData",
            "period": 1.0,
            "scale": "week",
            "unit" : "MB",
            "category": "Disk",
            "chart" : True,
        },
        {
            "name" : "oneMonthDiskSizeGrowth",
            "description" : "one month disk size usage growth",
            "counter" : "couch_total_disk_size",
            "code" : "GrowthChartData",
            "period": 1.0,
            "scale": "month",
            "unit" : "MB",
            "category": "Disk",
            "chart" : True,
        },
        {
            "name" : "threeMonthDiskSizeGrowth",
            "description" : "3 month disk usage growth",
            "counter" : "couch_total_disk_size",
            "code" : "GrowthChartData",
            "period": .25,
            "scale": "year",
            "unit" : "MB",
            "category": "Disk",
            "chart" : True,
        },
        {
            "name" : "sixMonthDiskSizeGrowth",
            "description" : "6 month disk usage growth",
            "counter" : "couch_total_disk_size",
            "code" : "GrowthChartData",
            "period": .5,
            "scale": "year",
            "unit" : "MB",
            "category": "Disk",
            "chart" : True,
        },
        {
            "name" : "nineMonthDiskSizeGrowth",
            "description" : "9 month disk usage growth",
            "counter" : "couch_total_disk_size",
            "code" : "GrowthChartData",
            "period": .75,
            "scale": "year",
            "unit" : "MB",
            "category": "Disk",
            "chart" : True,
        },
     ],
     "sizing": True,
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


