import os
import sys
import datetime
import logging
import traceback
import string

import util_cli as util
import cluster_stats
import diskqueue_stats
import node_stats
import stats_buffer
import threshold
import prescription

from Cheetah.Template import Template

capsules = [
    (node_stats.NodeCapsule, "node_stats", "NodeCapsule"),
    (cluster_stats.ClusterCapsule, "cluster_stats", "ClusterCapsule"),
    #(bucket_stats.BucketCapsule, "bucket_stats", "BucketCapsule"),
    (diskqueue_stats.DiskQueueCapsule, "diskqueue_stats", "DiskQueueCapsule"),
]

globals = {
    "versions" : "1.0",
    "report_time" : datetime.datetime.now(),
    "cluster_health" : "ok",
}

node_list = {}
bucket_list = {}
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
            bucket_list[bucket] = "OK"
            bucket_symptoms[bucket] = []
            bucket_node_symptoms[bucket] = {}
            bucket_node_status[bucket] = {}

        for capsule, package_name, capsule_name in capsules:
            for pill in capsule:
                self.log.debug(pill['name'])
                for counter in pill['ingredients']:
                    try:
                        result = eval("{0}.{1}().run(counter, threshold.{2})".format(package_name, counter['code'], capsule_name))
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
                                status = "OK"
                                for val in values:
                                    if val[0] == "error":
                                        status = "Error"
                                        break
                                    elif val[0] == "warn":
                                        status = "Warning"
                                        break
                                for val in values:
                                    if val[0] == "variance" or val[0] == "error":
                                        continue
                                    elif val[0] == "total":
                                        bucket_symptoms[bucket].append({"description":counter["description"], "value":val[1], "status":status})
                                    else:
                                        if bucket_node_symptoms[bucket].has_key(val[0]) == False:
                                            bucket_node_symptoms[bucket][val[0]] = []
                                        bucket_node_symptoms[bucket][val[0]].append({"description" : counter["description"], "value" : val[1], "status":status})

                        if pill.has_key("perNode") and pill["perNode"] :
                            node_symptoms[counter["name"]] = {"description" : counter["description"], "value":result}
                        if pill.has_key("nodewise") and pill["nodewise"]:
                            node_list[counter["name"]] = {"description" : counter["description"], "value":result}
                        if pill.has_key("nodeDisparate") and pill["nodeDisparate"] :
                            for bucket,values in result.iteritems():
                                if bucket == "cluster":
                                    continue
                                for val in values:
                                    if val[0] == "total":
                                        continue;
                                    if val[0] == "variance" and val[1] != 0:
                                        node_disparate[counter["name"]] = {"description" : counter["description"], "bucket": bucket, "value":values}
                        if pill.has_key("indicator") and pill["indicator"]:
                            if len(result) > 0:
                                cause = impact = action = "To be defined"
                                try:
                                    cause = prescription.Capsules[pill['name']]["cause"]
                                    impact = prescription.Capsules[pill['name']]["impact"]
                                    action = prescription.Capsules[pill['name']]["action"]
                                except Exception, e:
                                    print e
                                for bucket,values in result.iteritems():
                                    if type(values) is dict:
                                        if values.has_key("error"):
                                            if indicator_error.has_key(counter["name"]) == False:
                                                indicator_error[counter["name"]] = []
                                            indicator_error[counter["name"]].append({"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":values["error"], 
                                                                            "cause" : cause,
                                                                            "impact" : impact,
                                                                            "action" : action,
                                                                           })
                                            for val in values["error"]:
                                                bucket_node_status[bucket][val["node"]] = "Error"
                                                bucket_list[bucket] = "Error"
                                        if values.has_key("warn"):
                                            if indicator_warn.has_key(counter["name"]) == False:
                                                indicator_warn[counter["name"]] = []
                                            indicator_warn[counter["name"]].append({"description" : counter["description"],
                                                                           "bucket": bucket,
                                                                           "value":values["warn"],
                                                                           "cause" : cause,
                                                                           "impact" : impact,
                                                                           "action" : action,
                                                                          })
                                            for val in values["warn"]:
                                                if bucket_node_status[bucket].has_key(node["node"]) == False:
                                                    bucket_node_status[bucket][node["node"]] = "Warning"
                                                if bucket_list[bucket] == "OK":
                                                    bucket_list[bucket] = "Warning"
                                    elif type(values) is list:
                                        for val in values:
                                            if val[0] == "error":
                                                if indicator_error.has_key(counter["name"]) == False:
                                                    indicator_error[counter["name"]] = []
                                                indicator_error[counter["name"]].append({"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":val[1], 
                                                                            "cause" : cause,
                                                                            "impact" : impact,
                                                                            "action" : action,
                                                                           })
                                                for node in val[1]:
                                                    bucket_node_status[bucket][node["node"]] = "Error"
                                                    bucket_list[bucket] = "Error"
                                            elif val[0] == "warn":
                                                if indicator_warn.has_key(counter["name"]) == False:
                                                    indicator_warn[counter["name"]] = []
                                                indicator_warn[counter["name"]].append({"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":val[1], 
                                                                            "cause" : cause,
                                                                            "impact" : impact,
                                                                            "action" : action,
                                                                           })
                                                for node in val[1]:
                                                    if bucket_node_status[bucket].has_key(node["node"]) == False:
                                                        bucket_node_status[bucket][node["node"]] = "Warning"
                                                    if bucket_list[bucket] == "OK":
                                                        bucket_list[bucket] = "Warning"
                    except Exception, err:
                        self.log.error("Exception launched when processing counter: {0}".format(counter["name"]))
                        traceback.print_exc()

        if len(indicator_error) > 0:
            globals["cluster_health"] = "Error"
        elif len(indicator_warn) > 0:
            globals["cluster_health"] = "Warning"
        else:
            globals["cluster_health"] = "OK"

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
            "indicator_warn_exist" : len(indicator_warn) > 0,
            "indicator_error" : indicator_error,
            "indicator_error_exist" : len(indicator_error) > 0,
            "verbose" : verbose,
        }

        # read the current version number
        try:
            f = open('VERSION.txt', 'r')
            globals["versions"] = string.strip(f.read())
            f.close()
        except Exception:
            pass

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

        mydir = os.path.dirname(sys.argv[0])
        f = open(htmlfile, 'w')
        print >> f, Template(file=os.path.join(mydir, "report-htm.tmpl"), searchList=[dict])
        f.close()

        sys.stderr.write("\nThe run finished successfully. Please find html output at '{0}' and text output at '{1}'.\n".format(htmlfile, txtfile))