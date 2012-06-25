#!/usr/bin/python
# -*- coding: utf-8 -*-

Capsules = {
    "CacheMissRatio" : {
        "cause" : "To be defined",
        "impact" : "It will result in too many background fetches from disk and lead to poor IO performance",
        "action" : "Please contact support@couchbase.com",
    },
    "ActiveReplicaResidentRatio" : {
        "cause" : "To be defined",
        "impact" : "Failovers will slow down nodes severely because backfills from disk will be required and result in eviction of active items",
        "action" : "Please contact support@couchbase.com",
    },
    "VBucketNumber" : {
        "cause" : "To be defined",
        "impact" : "Data is missing",
        "action" : "Run rebalance o recreate missing vBuckets",
    },
    "RebalancePerformance" : {
        "cause" : "Tap queue backfill remaining is higher than threshold.",
        "impact" : "To be defined",
        "action" : "Please contact support@couchbase.com",
    },
    "MemoryFragmentation" : {
        "cause" : "Severe IO issue possibly caused by fragmentation",
        "impact" : "To be defined",
        "action" : "Please contact support@couchbase.com",
    },
    "EPEnginePerformance" : {
        "cause" : "Poor engine KPIs",
        "impact" : "To be defined",
        "action" : "Please contact support@couchbase.com",
    },
    "DiskQueueDiagnosis" : {
        "cause" : "Disk write queue backed up",
        "impact" : "Data will be lost if the node goes down",
        "action" : "Please contact support@couchbase.com",
    },
    "ReplicationTrend" : {
        "cause" : "Ratio of items in the replication queue and active items greater than threshold",
        "impact" : "If the nodes fails over, data will be missing on the replica",
        "action" : "Do not failover the node",
    },
    "DiskQueueDrainingAnalysis" :{
        "cause" : "To be defined",
        "impact" : "To be defined",
        "action" : "Please contact support@couchbase.com",
    },
}

