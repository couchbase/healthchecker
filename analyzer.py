import os
import sys
import datetime
import logging
import traceback
import string
import fnmatch

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

class UtilTool:
    def isdict(self, obj):
        return isinstance(obj, dict)

    def statsClass(self, status, hasOkStatus=True):
        if status == "Error":
            return ["status-error", "Immediate action needed"]
        elif status == "Warning":
            return ["status-warning", "Attention needed"]
        else:
            if hasOkStatus:
                return ["status-ok", "OK"]
            else:
                return ["", "OK"]
class StatsAnalyzer:
    def __init__(self, log):
        self.log = log

    def run_analysis(self, scale):

        for bucket in stats_buffer.buckets.iterkeys():
            bucket_type =  stats_buffer.bucket_info[bucket]['bucketType']
            bucket_list[bucket] = {"status":"OK", "type":bucket_type, "anchor":None}
            bucket_symptoms[bucket] = []
            bucket_node_symptoms[bucket] = {}
            bucket_node_status[bucket] = {}

        for capsule, package_name, capsule_name in capsules:
            for pill in capsule:
                self.log.debug(pill['name'])
                for counter in pill['ingredients']:
                    try:
                        result = eval("{0}.{1}().run(counter, scale, threshold.{2})".format(package_name, counter['code'], capsule_name))
                        self.log.debug(counter)
                        if pill.has_key("clusterwise") and pill["clusterwise"] :
                            if isinstance(result, dict):
                                if result.has_key("cluster"):
                                    cluster_symptoms[counter["name"]] = {"description" : counter["description"], "value":result["cluster"]}
                                else:
                                    cluster_symptoms[counter["name"]] = {"description" : counter["description"], "value":result}
                            else:
                                cluster_symptoms[counter["name"]] = {"description" : counter["description"], "value":result}
                            if counter.has_key("formula"):
                                cluster_symptoms[counter["name"]]["formula"] = counter["formula"]
                            else:
                                cluster_symptoms[counter["name"]]["formula"] = "N/A"
                        if pill.has_key("perBucket") and pill["perBucket"] :
                            for bucket, values in result.iteritems():
                                if bucket == "cluster":
                                    continue
                                bucket_status = "OK"
                                node_error = []
                                node_warn = []
                                for val in values:
                                    if val[0] == "error":
                                        bucket_status = "Error"
                                        for node in val[1]:
                                            node_error.append(node["node"])
                                        break
                                    if val[0] == "warn":
                                        bucket_status = "Warning"
                                        for node in val[1]:
                                            node_warn.append(node["node"])
                                        break
                                for val in values:
                                    if val[0] == "variance" or val[0] == "error" or val[0] == "warn":
                                        continue
                                    elif val[0] == "total":
                                        if counter.has_key("formula"):
                                            bucket_symptoms[bucket].append({"description":counter["description"], 
                                                                            "value":val[1], 
                                                                            "status":bucket_status, 
                                                                            "formula":counter["formula"]})
                                        else:
                                            bucket_symptoms[bucket].append({"description":counter["description"], 
                                                                            "value":val[1], 
                                                                            "status":bucket_status,
                                                                            "formula":"N/A"})
                                    else:
                                        if bucket_node_symptoms[bucket].has_key(val[0]) == False:
                                            bucket_node_symptoms[bucket][val[0]] = []
                                        counter_status = "OK"
                                        if val[0] in node_warn:
                                            counter_status = "Warning"
                                        if val[0] in node_error:
                                            counter_status = "Error"
                                        if counter.has_key("formula"):
                                            bucket_node_symptoms[bucket][val[0]].append({"description" : counter["description"], 
                                                                                         "value" : val[1], 
                                                                                         "status":counter_status,
                                                                                         "formula":counter["formula"]})
                                        else:
                                            bucket_node_symptoms[bucket][val[0]].append({"description" : counter["description"], 
                                                                                         "value" : val[1], 
                                                                                         "status":counter_status,
                                                                                         "formula":"N/A"})
                        if pill.has_key("perNode") and pill["perNode"] :
                            if counter.has_key("formula"):
                                node_symptoms[counter["name"]] = {"description" : counter["description"], 
                                                                  "value":result, 
                                                                  "formula":counter["formula"]}
                            else:
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
                                            if counter.has_key("formula"):
                                                indicator_error[counter["name"]].append({"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":values["error"], 
                                                                            "cause" : cause,
                                                                            "impact" : impact,
                                                                            "action" : action,
                                                                            "formula" : counter["formula"],
                                                                           })
                                            else:
                                                indicator_error[counter["name"]].append({"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":values["error"], 
                                                                            "cause" : cause,
                                                                            "impact" : impact,
                                                                            "action" : action,
                                                                            "formula": "N/A",
                                                                           })
                                            for val in values["error"]:
                                                bucket_node_status[bucket][val["node"]] = "Error"
                                                bucket_list[bucket]["status"] = "Error"
                                                bucket_list[bucket]["anchor"] = "counter_%s_%s_%s" % (bucket, val["node"], counter["name"])
                                        if values.has_key("warn"):
                                            if indicator_warn.has_key(counter["name"]) == False:
                                                indicator_warn[counter["name"]] = []
                                            if counter.has_key("formula"):
                                                indicator_warn[counter["name"]].append({"description" : counter["description"],
                                                                           "bucket": bucket,
                                                                           "value":values["warn"],
                                                                           "cause" : cause,
                                                                           "impact" : impact,
                                                                           "action" : action,
                                                                           "formula" : counter["formula"],
                                                                          })
                                            else:
                                                indicator_warn[counter["name"]].append({"description" : counter["description"],
                                                                           "bucket": bucket,
                                                                           "value":values["warn"],
                                                                           "cause" : cause,
                                                                           "impact" : impact,
                                                                           "action" : action,
                                                                           "formula": "N/A",
                                                                          })
                                            for node in values["warn"]:
                                                node_val = None
                                                if type(node) is dict:
                                                    node_val = node["node"]
                                                else:
                                                    node_val = node[0]
                                                if bucket_node_status[bucket].has_key(node_val) == False:
                                                    bucket_node_status[bucket][node_val] = "Warning"
                                                if bucket_list[bucket]["status"] == "OK":
                                                    bucket_list[bucket]["status"] = "Warning"
                                                    bucket_list[bucket]["anchor"] = "counter_%s_%s_%s" % (bucket, node_val, counter["name"])
                                    elif type(values) is list:
                                        for val in values:
                                            if val[0] == "error":
                                                if indicator_error.has_key(counter["name"]) == False:
                                                    indicator_error[counter["name"]] = []
                                                if counter.has_key("formula"):
                                                    indicator_error[counter["name"]].append({"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":val[1], 
                                                                            "cause" : cause,
                                                                            "impact" : impact,
                                                                            "action" : action,
                                                                            "formula": counter["formula"],
                                                                           })
                                                else:
                                                    indicator_error[counter["name"]].append({"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":val[1], 
                                                                            "cause" : cause,
                                                                            "impact" : impact,
                                                                            "action" : action,
                                                                            "formula" : "N/A",
                                                                           })
                                                for node in val[1]:
                                                    bucket_node_status[bucket][node["node"]] = "Error"
                                                    bucket_list[bucket]["status"] = "Error"
                                                    bucket_list[bucket]["anchor"] = "counter_%s_%s_%s" % (bucket, node["node"], counter["name"])
                                            elif val[0] == "warn":
                                                if indicator_warn.has_key(counter["name"]) == False:
                                                    indicator_warn[counter["name"]] = []
                                                if counter.has_key("formula"):
                                                    indicator_warn[counter["name"]].append({"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":val[1], 
                                                                            "cause" : cause,
                                                                            "impact" : impact,
                                                                            "action" : action,
                                                                            "formula": counter["formula"],
                                                                           })
                                                else:
                                                    indicator_warn[counter["name"]].append({"description" : counter["description"], 
                                                                            "bucket": bucket, 
                                                                            "value":val[1], 
                                                                            "cause" : cause,
                                                                            "impact" : impact,
                                                                            "action" : action,
                                                                            "formula" : "N/A",
                                                                           })
                                                for node in val[1]:
                                                    if bucket_node_status[bucket].has_key(node["node"]) == False:
                                                        bucket_node_status[bucket][node["node"]] = "Warning"
                                                    if bucket_list[bucket]["status"] == "OK":
                                                        bucket_list[bucket]["status"] = "Warning"
                                                        bucket_list[bucket]["anchor"] = "counter_%s_%s_%s" % (bucket, node["node"], counter["name"])
                    except Exception, err:
                        self.log.error("Exception launched when processing counter: {0}".format(counter["name"]))
                        traceback.print_exc()

        if len(indicator_error) > 0:
            globals["cluster_health"] = "Error"
        elif len(indicator_warn) > 0:
            globals["cluster_health"] = "Warning"
        else:
            globals["cluster_health"] = "OK"

    def run_report(self, txtfile, htmlfile, verbose, scale, debug):
        reports_dir = os.path.join(os.path.dirname(sys.argv[0]), 'reports')
        txtfile = os.path.join(reports_dir, txtfile)
        htmlfile = os.path.join(reports_dir, htmlfile)

        dict = {
            "util": UtilTool(),
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
            "scale" : scale,
            "debug" : debug,
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

        #print util.pretty_print(bucket_node_symptoms)

        f = open(htmlfile, 'w')
        print >> f, Template(file=os.path.join(reports_dir, "template.tmpl"), searchList=[dict])
        f.close()

        # generate array/list of available reports for use via AJAX
        available_reports = [os.path.splitext(n)[0]
                             for n in fnmatch.filter(os.listdir('./reports/'),
                                                     '*.html')]
        f = open(os.path.join(reports_dir, 'all.json'), 'w')
        print >> f, util.pretty_print(available_reports)
        f.close()
