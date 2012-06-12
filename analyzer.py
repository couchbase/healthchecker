import sys
import datetime
import logging

import util_cli as util
import cluster_stats
import diskqueue_stats
import node_stats
import stats_buffer

from Cheetah.Template import Template

capsules = [
    (node_stats.NodeCapsule, "node_stats"),
    (cluster_stats.ClusterCapsule, "cluster_stats"),
    #(bucket_stats.BucketCapsule, "bucket_stats"),
    (diskqueue_stats.DiskQueueCapsule, "diskqueue_stats"),
]

globals = {
    "versions" : "1.0",
    "report_time" : datetime.datetime.now(),
    "cluster_health" : "ok",
}

node_list = {}
bucket_list = []
cluster_symptoms = {}
bucket_symptoms = {}
bucket_node_symptoms = {}
bucket_node_status = {}
node_symptoms = {}
indicator_error = {}
indicator_warn = {}
node_disparate = {}

class StatsAnalyzer:
    def __init__(self, log):
        self.log = log

    def run_analysis(self):

        for bucket in stats_buffer.buckets.iterkeys():
            bucket_list.append(bucket)
            bucket_symptoms[bucket] = []
            bucket_node_symptoms[bucket] = {}
            bucket_node_status[bucket] = {}

        for capsule, package_name in capsules:
            for pill in capsule:
                self.log.debug(pill['name'])
                for counter in pill['ingredients']:
                    result = eval("{0}.{1}().run(counter)".format(package_name, counter['code']))

                    self.log.debug(counter)
                    if pill.has_key("clusterwise") and pill["clusterwise"] :
                        if isinstance(result, dict):
                            if result.has_key("cluster"):
                                cluster_symptoms[counter["name"]] = {"description" : counter["description"], "value":result["cluster"]}
                            else:
                                cluster_symptoms[counter["name"]] = {"description" : counter["description"], "value":result}
                        else:
                            cluster_symptoms[counter["name"]] = {"description" : counter["description"], "value":result}
                    if pill.has_key("perBucket") and pill["perBucket"] :
                        for bucket, values in result.iteritems():
                            if bucket == "cluster":
                                continue
                            for val in values:
                                if val[0] == "variance" or val[0] == "error":
                                    continue
                                elif val[0] == "total":
                                    bucket_symptoms[bucket].append({"description" : counter["description"], "value" : values[-1][1]})
                                else:
                                    if bucket_node_symptoms[bucket].has_key(val[0]) == False:
                                        bucket_node_symptoms[bucket][val[0]] = []
                                    bucket_node_symptoms[bucket][val[0]].append({"description" : counter["description"], "value" : val[1]})

                    if pill.has_key("perNode") and pill["perNode"] :
                        node_symptoms[counter["name"]] = {"description" : counter["description"], "value":result}
                    if pill.has_key("nodewise") and pill["nodewise"]:
                        node_list[counter["name"]] = {"description" : counter["description"], "value":result}
                    
                    if pill.has_key("indicator"):
                        if len(result) > 0:
                            for bucket,values in result.iteritems():
                                if type(values) is dict:
                                    if values.has_key("error"):
                                        indicator_error[counter["name"]] = {"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":values["error"], 
                                                                            "cause" : pill["indicator"]["cause"],
                                                                            "impact" : pill["indicator"]["impact"],
                                                                            "action" : pill["indicator"]["action"],
                                                                           }
                                        for val in values["error"]:
                                            bucket_node_status[bucket][val["node"]] = "error"
                                            
                                    if values.has_key("warn"):
                                        indicator_warn[counter["name"]] = {"description" : counter["description"],
                                                                           "bucket": bucket,
                                                                           "value":values["warn"],
                                                                           "cause" : pill["indicator"]["cause"],
                                                                           "impact" : pill["indicator"]["impact"],
                                                                           "action" : pill["indicator"]["action"],
                                                                          }
                                elif type(values) is list:
                                    for val in values:
                                        if val[0] == "error":
                                            indicator_error[counter["name"]] = {"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":val[1], 
                                                                            "cause" : pill["indicator"]["cause"],
                                                                            "impact" : pill["indicator"]["impact"],
                                                                            "action" : pill["indicator"]["action"],
                                                                           }
                                            for val in values["error"]:
                                                bucket_node_status[bucket][val["node"]] = "error"
                                        elif val[0] == "warn":
                                            indicator_warn[counter["name"]] = {"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":val[1], 
                                                                            "cause" : pill["indicator"]["cause"],
                                                                            "impact" : pill["indicator"]["impact"],
                                                                            "action" : pill["indicator"]["action"],
                                                                           }
                    if pill.has_key("nodeDisparate") and pill["nodeDisparate"] :
                        for bucket,values in result.iteritems():
                            if bucket == "cluster":
                                continue
                            for val in values:
                                if val[0] == "total":
                                    continue;
                                if val[0] == "variance" and val[1] != 0:
                                    node_disparate[counter["name"]] = {"description" : counter["description"], "bucket": bucket, "value":values}

        if len(indicator_error) > 0:
            globals["cluster_health"] = "error"
        elif len(indicator_warn) > 0:
            globals["cluster_health"] = "warning"

    def run_report(self, txtfile, htmlfile, verbose):
        
        dict = {
            "globals" : globals,
            "cluster_symptoms" : cluster_symptoms,
            "bucket_symptoms" : bucket_symptoms,
            "bucket_node_symptoms" : bucket_node_symptoms,
            "bucket_node_status" : bucket_node_status,
            "node_symptoms" : node_symptoms,
            "node_list" : node_list,
            "bucket_list" : bucket_list,
            "indicator_warn" : indicator_warn,
            "indicator_error" : indicator_error,
            "verbose" : verbose,
        }
        
        f = open(txtfile, 'w')
        report = {}
        report["Report Time"] = globals["report_time"].strftime("%Y-%m-%d %H:%M:%S")
        
        report["Nodelist Overview"] = node_list
            
        report["Cluster Overview"] = cluster_symptoms
        
        report["Bucket Metrics"] = bucket_symptoms

        report["Bucket Node Metrics"] = bucket_node_symptoms
        
        report["Key indicators"] = (indicator_error, indicator_warn)
        
        report["Node disparate"] = node_disparate

        print >> f, util.pretty_print(report)
        f.close()
        
        f = open(htmlfile, 'w')
        print >> f, Template(file="report-htm.tmpl", searchList=[dict])
        f.close()

        sys.stderr.write("\nThis run finishes successfully. Please find output result at '{0}'".format(htmlfile))