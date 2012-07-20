#!/usr/bin/python
# -*- coding: utf-8 -*-

Capsules = {
    "CacheMissRatio" : {
        "cause" : "Too many requests for information that has already been ejected to disk.",
        "impact" : "Results in too many fetchs from disk, causing poor performance and slower I/O.",
        "action" : "Increase disk quota for buckets, or add nodes to cluster. If issue persists please contact support@couchbase.com",
    },
    "ActiveReplicaResidentRatio" : {
        "cause" : "Too much data on disk versus data in memory.",
        "impact" : "Performing failover will slow down nodes severely because it requires information stored on disk and result in eviction of active items",
        "action" : "Increase disk quota for buckets, or add nodes to cluster. If issue persists please contact support@couchbase.com",
    },
    "VBucketNumber" : {
        "cause" : "The number of vBuckets is less than the maximum number. This can occur if a node goes down.",
        "impact" : "The cluster is unbalanced. Data is missing and unavailable. Writes to missing vBuckets will fail.",
        "action" : "Run rebalance to recreate missing vBuckets. If issue persists please contact support@couchbase.com",
    },
    "VBucketServerMap" : {
        "cause" : "vBucketServerMap sanity checking fails",
        "impact" : "Rebalance may fail",
        "action" : "Please contact support@couchbase.com",
    },
    "RebalancePerformance" : {
        "cause" : "Amount of data that should be moved between nodes, called TAP Queue, is is higher than threshold.",
        "impact" : "Rebalances will take long time, freeze, or may fail due to timeout.",
        "action" : "Wait for TAP Queue to decrease, if it does not, please contact support@couchbase.com",
    },
    "MemoryFragmentation" : {
        "cause" : "Severe IO issue possibly caused by in-memory fragmentation",
        "impact" : "Overuse of RAM for a node, causing ejections to disk. Possible system out of memory errors; OS may shutdown entire Couchbase Server.",
        "action" : "Remove problem node, and add again the node to cluster. If issue persists, please contact support@couchbase.com",
    },
    "DiskFragmentation" : {
        "cause" : "Severe IO issue possibly caused by disk fragmentation or limited disk space",
        "impact" : "OS may shutdown entire Couchbase Server.",
        "action" : "Remove problem node, and add again the node to cluster. If issue persists, please contact support@couchbase.com",
    },
    "EPEnginePerformance" : {
        "cause" : "Poor engine Key Performance Indicators",
        "impact" : "To be defined",
        "action" : "Please contact support@couchbase.com",
    },
    "DiskQueueDiagnosis" : {
        "cause" : "Disk write queue overloaded",
        "impact" : "Data is available in memory but any data in the queue waiting to be persisted will be lost if the node goes down",
        "action" : "Increase disk quota for buckets, or add nodes to cluster. Can remove and re-add a server to resolve a disk fragmentation issue. If issue persists please contact support@couchbase.com"
    },
    "ReplicationTrend" : {
        "cause" : "Ratio of items in the replication queue and active items greater than threshold.",
        "impact" : "If the nodes fails over, data will be missing on the replica. If you failover, information in the replication queue will be lost.",
        "action" : "Do not failover the node. Wait until replication queue is low to failover. If replication queue remains high, contact support@couchbase.com",
    },
    "DiskQueueDrainingAnalysis" :{
        "cause" : "Drain rate from RAM to disk is too slow; can be caused by disk fragmentation.",
        "impact" : "Rate of data persisted from RAM to disk is too high.",
        "action" : "Do not failover until drain rate is faster. Increase disk quota, add nodes to cluster, or remove and re-add a node. Please contact support@couchbase.com",
    },
}