import dbaccessor
import stats_buffer
import util
 
class OpsRatio:
    def run(self, accessor):        
        ops_avg = {
            "cmd_get": [],
            "cmd_set": [],
            "delete_hits" : [],
        }
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            for counter in accessor["counter"]:
                values = stats_info[accessor["scale"]][counter]
                nodeStats = values["nodeStats"]
                samplesCount = values["samplesCount"]
                total = 0
                for node, vals in nodeStats.iteritems():
                    avg = sum(vals) / samplesCount
                    total = total + avg
                    ops_avg[counter].append((bucket, node, avg))
                ops_avg[counter].append((bucket, "total", total / len(nodeStats)))
        result = []
        for read, write, delete in zip(ops_avg['cmd_get'], ops_avg['cmd_set'], ops_avg['delete_hits']):

            total = read[2] + write[2] + delete[2]
            if total == 0:
                result.append((read[0], read[1], "0:0:0"))
            else:
                read_ratio = read[2] *100 / total 
                write_ratio = write[2] * 100 / total
                del_ratio = delete[2] * 100 /total
                result.append((read[0], read[1], "{0}% reads : {1}% writes : {2}% deletes".format(read_ratio, write_ratio, del_ratio)))

        return result

class ARRatio:
    def run(self, accessor):        
        ops_avg = {
            "vb_active_resident_items_ratio": [],
            "vb_replica_resident_items_ratio": [],
        }
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            for counter in accessor["counter"]:
                values = stats_info[accessor["scale"]][counter]
                nodeStats = values["nodeStats"]
                samplesCount = values["samplesCount"]
                total = 0
                for node, vals in nodeStats.iteritems():
                    avg = sum(vals) / samplesCount
                    total = total + avg
                    ops_avg[counter].append((node, avg))
                ops_avg[counter].append(("total", total / len(nodeStats)))
        result = []
        for active, replica in zip(ops_avg['vb_active_resident_items_ratio'], ops_avg['vb_replica_resident_items_ratio']):
            total = active[1] + replica[1]
            if total == 0:
                result.append((active[0], "0:0"))
            else:
                active_ratio = active[1] *100 / total 
                replica_ratio = replica[1] * 100 / total
                result.append((active[0], "{0}:{1}".format(active_ratio, replica_ratio)))

        return result

class CacheMissRatio:
    def run(self, accessor):
        trend = []
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[accessor["scale"]][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                a, b = util.linreg(timestamps, vals)
                trend.append((bucket, node, a, b))
        return trend

class ItemGrowth:
    def run(self, accessor):
        trend = []
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            values = stats_info[accessor["scale"]][accessor["counter"]]
            timestamps = values["timestamp"]
            timestamps = [x - timestamps[0] for x in timestamps]
            nodeStats = values["nodeStats"]
            samplesCount = values["samplesCount"]
            for node, vals in nodeStats.iteritems():
                a, b = util.linreg(timestamps, vals)
                avg = sum(vals) / samplesCount
                trend.append((bucket, node, a, b, avg))
        return trend

class AvgItemSize:
    def run(self, accessor):
        return 0

class NumVbuckt:
    def run(self, accessor):
        result = {}
        for bucket, stats_info in stats_buffer.buckets.iteritems():
            num_error = []
            total, values = stats_buffer.retrieveSummaryStats(bucket, accessor["counter"])
            values = stats_info[accessor["scale"]][accessor["counter"]]
            nodeStats = values["nodeStats"]
            for node, vals in nodeStats.iteritems():
                if vals[-1] < accessor["threshold"]:
                    num_error.append({"node":node, "value":vals[-1]})
            if len(num_error) > 0:
                result[bucket] = {"error" : num_error}
        return result

BucketCapsule = [
    {"name" : "bucketList",
     "ingredients" : [
        {
            "name" : "bucketList",
            "description" : "Bucket list",
            "type" : "pythonSQL",
            "code" : "BucketList",
        },
     ],
     "perBucket" : True,
    },
    {"name" : "CacheMissRatio",
     "ingredients" : [
        {
            "description" : "Cache miss ratio",
            "counter" : "ep_cache_miss_rate",
            "type" : "python",
            "scale" : "hour",
            "code" : "CacheMissRatio",
            "unit" : "percentage",
        },
     ]
    },
    {"name" : "Active / Replica Resident Ratio",
     "ingredients" : [
        {
            "description" : " A/R Ratio",
            "type" : "python",
            "scale" : "minute",
            "counter" : ["vb_active_resident_items_ratio", "vb_replica_resident_items_ratio"],
            "code" : "ARRatio",
        },
     ]
    },
    {"name" : "OPS performance",
     "ingredients" : [
        {
            "description" : "Read/Write/Delete ops ratio",
            "type" : "python",
            "scale" : "minute",
            "counter" : ["cmd_get", "cmd_set", "delete_hits"],
            "code" : "OpsRatio",
        },
     ]
    },
    {"name" : "Growth Rate",
     "ingredients" : [
        {
            "description" : "Data Growth rate for items",
            "counter" : "curr_items",
            "type" : "python",
            "scale" : "day",
            "code" : "ItemGrowth",
            "unit" : "percentage",
        },
     ]
    },
    {"name" : "Average Document Size",
     "ingredients" : [
        {
            "description" : "Average Document Size",
            "type" : "python",
            "code" : "AvgItemSize",
            "unit" : "KB",
        },
     ]
    },
    {"name" : "VBucket number",
     "ingredients" : [
        {
            "description" : "Active VBucket number",
            "counter" : "vb_active_num",
            "type" : "python",
            "scale" : "hour",
            "code" : "NumVbuckt"
        },
        {
            "description" : "Replica VBucket number",
            "counter" : "vb_replica_num",
            "type" : "python",
            "scale" : "hour",
            "code" : "NumVbuckt"
        },
     ]
    },
]


