import datetime
import fnmatch
import logging
import re
import string
import shutil
import traceback
import os
import sys

import cluster_stats
import diskqueue_stats
import node_stats
import stats_buffer
import threshold
import prescription
import util_cli as util

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
    "scale" : "all",
}

TEMPLATE_FILE = "template.tmpl"
CHART_FILE = "chart.tmpl"

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
sizing_symptoms = {}

class UtilTool:
    def isdict(self, obj):
        return isinstance(obj, dict)

    def islist(self, obj):
        return isinstance(obj, list)

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

    def activeTab(self, tab):
        if tab == globals["scale"]:
            return "active"
        else:
            return ""

class StatsAnalyzer:
    def __init__(self, log):
        self.log = log

    def init(self):
        for bucket in stats_buffer.buckets.iterkeys():
            bucket_type =  stats_buffer.bucket_info[bucket]['bucketType']
            bucket_list[bucket] = {"status":"OK", "type":bucket_type, "anchor":None}
            bucket_symptoms[bucket] = []
            bucket_node_symptoms[bucket] = {}
            bucket_node_status[bucket] = {}

        for node in stats_buffer.nodes.iterkeys():
            node_list[node] = {}
            sizing_symptoms[node] = {}
 
    def run_analysis(self, scale):
        self.init()

        for capsule, package_name, capsule_name in capsules:
            for pill in capsule:
                self.log.debug(pill['name'])
                for counter in pill['ingredients']:
                    try:
                        #eval_str = "{0}.{1}().run(counter, scale, threshold.{2})".format(package_name, counter['code'], capsule_name)
                        #print eval_str
                        result = eval("%s.%s().run(counter, scale, threshold.%s)" % (package_name, counter['code'], capsule_name))
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
                                if bucket == "cluster" or bucket == "_sizing":
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
                                            
                                        if isinstance(val[1], dict) and val[1].has_key("counter"):
                                            description = "%s - %s" % (counter["description"], val[1]["counter"])
                                        else:
                                            description = counter["description"]
                                        if counter.has_key("formula"):
                                            bucket_node_symptoms[bucket][val[0]].append({"description" : description, 
                                                                                         "value" : val[1], 
                                                                                         "status":counter_status,
                                                                                         "formula":counter["formula"]})
                                        else:
                                            bucket_node_symptoms[bucket][val[0]].append({"description" : description, 
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
                            for node, values in result.iteritems():
                                node_list[node] = {"description": counter["description"], "value": values}
                        if pill.has_key("sizing") and pill["sizing"]:
                            if result:
                                if result.has_key("_sizing"):
                                    sizing_result = result["_sizing"]
                                else:
                                    sizing_result = result
                                for node, value in sizing_result.iteritems():
                                    if not sizing_symptoms[node].has_key(counter["category"]):
                                        sizing_symptoms[node][counter["category"]] = []
                                    withchart = False
                                    if counter.has_key("chart"):
                                        withchart = counter["chart"]
                                    chart_id = "c_%s_%s" % (counter["name"], node)
                                    if counter.has_key("unit"):
                                        unit = counter["unit"]
                                    else:
                                        unit = ""
                                    sizing_symptoms[node][counter["category"]].append(
                                                                 {"description": counter["description"],
                                                                  "unit": unit,
                                                                  "value": value,
                                                                  "category": counter["category"],
                                                                  "chart": withchart,
                                                                  "chart_id": re.sub('[.:]', '_', chart_id),
                                                                  })

                        if pill.has_key("nodeDisparate") and pill["nodeDisparate"] :
                            for bucket,values in result.iteritems():
                                if bucket == "cluster" or bucket == "_sizing":
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
                        self.log.error("Exception launched when processing counter: %s" % counter["name"])
                        traceback.print_exc()

        if len(indicator_error) > 0:
            globals["cluster_health"] = "Error"
        elif len(indicator_warn) > 0:
            globals["cluster_health"] = "Warning"
        else:
            globals["cluster_health"] = "OK"

    def run_report(self, verbose, scale_set, scale, debug, output_dir):
        reports_dir = os.path.join(os.path.dirname(sys.argv[0]), 'reports')
        txtfile = os.path.join(output_dir, scale + ".txt")
        htmlfile = os.path.join(output_dir, scale + ".html")

        dict = {
            "util": UtilTool(),
            "globals" : globals,
            "cluster_symptoms" : cluster_symptoms,
            "bucket_symptoms" : bucket_symptoms,
            "bucket_node_symptoms" : bucket_node_symptoms,
            "bucket_node_status" : bucket_node_status,
            "node_symptoms" : node_symptoms,
            "sizing_symptoms": sizing_symptoms,
            "node_list" : node_list,
            "bucket_list" : bucket_list,
            "indicator_warn" : indicator_warn,
            "indicator_warn_exist" : len(indicator_warn) > 0,
            "indicator_error" : indicator_error,
            "indicator_error_exist" : len(indicator_error) > 0,
            "verbose" : verbose,
            "scale_set" : scale_set,
            "debug" : debug,
            "sizing": None,
        }
        globals["scale"] = scale

        # read the current version number
        for fname in [os.path.join(os.path.dirname(sys.argv[0]), '..', '..', 'VERSION.txt'), \
                      os.path.join(os.path.dirname(sys.argv[0]), '..', 'VERSION.txt'), \
                      os.path.join(os.path.dirname(sys.argv[0]), 'VERSION.txt')]:
            try:
                f = open(fname, 'r')
                globals["versions"] = string.strip(f.read())
                f.close()
            except Exception:
                pass

        f = open(txtfile, 'w')
        report = {}
        report["Report Time"] = globals["report_time"].strftime("%Y-%m-%d %H:%M:%S")
        report["Nodelist Overview"] = node_list
        report["Sizing Report"] = sizing_symptoms
        report["Cluster Overview"] = cluster_symptoms
        report["Bucket Metrics"] = bucket_symptoms
        report["Bucket Node Metrics"] = bucket_node_symptoms
        report["Key indicators"] = (indicator_error, indicator_warn)
        report["Node disparate"] = node_disparate

        print >> f, util.pretty_print(report)
        f.close()

        #print util.pretty_print(bucket_node_symptoms)

        f = open(htmlfile, 'w')
        print >> f, Template(file=os.path.join(reports_dir, TEMPLATE_FILE), searchList=[dict])
        f.close()

        #generate  charts if any
        for node in node_list:
            for category, values in sizing_symptoms[node].iteritems():
                for sizing in values:   
                    if sizing["chart"]:
                        dict["sizing"] = sizing
                        htmlfile = os.path.join(output_dir, sizing["chart_id"] + ".html")
                        f = open(htmlfile, "w")
                        print >> f, Template(file=os.path.join(reports_dir,  CHART_FILE), searchList=[dict])
                        f.close()

        # generate array/list of available reports for use via AJAX
        available_reports = [os.path.splitext(n)[0]
                             for n in fnmatch.filter(os.listdir('./reports/'),
                                                     '*.html')]
        f = open(os.path.join(output_dir, 'all.json'), 'w')
        print >> f, util.pretty_print(available_reports)
        f.close()

        #Need to copy support files for final report
        normalize_report_dir = os.path.normpath(reports_dir)
        normalize_output_dir = os.path.normpath(os.path.dirname(output_dir))
        if normalize_output_dir != normalize_report_dir:
            for item in os.listdir(normalize_report_dir):
                if not item in [TEMPLATE_FILE, CHART_FILE]:
                    s = os.path.join(normalize_report_dir, item)
                    d = os.path.join(normalize_output_dir, item)
                    try:
                        if os.path.isfile(s):
                            shutil.copy2(s, d)
                        else:
                            shutil.copytree(s, d)
                    except Exception:
                        pass

        sys.stderr.write("\nThe run finished successfully. \nPlease find html output at '%s' and text output at '%s'.\n" % \
            (htmlfile, txtfile))