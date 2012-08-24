#!/usr/bin/python
# -*- coding: utf-8 -*-

Capsules = {
    "CacheMissRatio" : {
        "cause" : "Too many requests for information that has already been ejected to disk.",
        "impact" : "Results in too many fetches from disk, causing poor performance and slower I/O.",
        "action" : "Increase disk quota for buckets, or add nodes to cluster. If issue persists please contact support@couchbase.com",
    },
    "ActiveReplicaResidentRatio" : {
        "cause" : "Too few replicated items",
        "impact" : "Performing failover will slow down nodes severely because it will likely require information stored on disk",
        "action" : "Increase disk quota for buckets, or add more nodes to cluster. If issue persists please contact support@couchbase.com",
    },
    "ResidentRatio" : {
        "cause" : "Not enough RAM in the cluster.",
        "impact" : "Performing failover will slow down nodes severely because it will likely require information stored on disk",
        "action" : "Increase disk quota for buckets, or add more nodes to cluster. If issue persists please contact support@couchbase.com",
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
        "cause" : "Amount of data that should be moved between nodes, called TAP Queue, is higher than threshold.",
        "impact" : "Rebalances will take long time, freeze, or may fail due to timeout.",
        "action" : "Wait for TAP Queue to decrease, if it does not, please contact support@couchbase.com",
    },
    "MemoryFragmentation" : {
        "cause" : "Severe IO issue possibly caused by in-memory fragmentation",
        "impact" : "Overuse of RAM for a node, causing ejections to disk. Possible system out of memory errors; OS may shutdown Couchbase Server.",
        "action" : "Remove problem node, and add again the node to cluster. If issue persists, please contact support@couchbase.com",
    },
    "DiskFragmentation" : {
        "cause" : "Severe IO issue possibly caused by disk fragmentation",
        "impact" : "OS may shutdown Couchbase Server if memory grows in persistence queues due to slow disk I/O.",
        "action" : "Replace problem node. If issue persists, please contact support@couchbase.com",
    },
    "EPEnginePerformance" : {
        "cause" : "Poor ep-engine key performance indicators",
        "impact" : "Server performance is below expectation.",
        "action" : "Please contact support@couchbase.com",
    },
    "DiskQueueDiagnosis" : {
        "cause" : "Persistence severely behind",
        "impact" : "Data is available in memory but any data in the queue waiting to be persisted will be lost if the node goes down",
        "action" : "Increase disk quota for buckets, or add nodes to cluster. Can remove and re-add a server to resolve a disk fragmentation issue. If issue persists please contact support@couchbase.com"
    },
    "ReplicationNumTrend" : {
        "cause" : "Replication queue overloaded",
        "impact" : "If the nodes fails over, data will be missing on the replica. If you failover, information in the replication queue will be lost.",
        "action" : "Do not failover the node. Wait until replication queue is low to failover. If replication queue remains high, contact support@couchbase.com",
    },
    "ReplicationPercentageTrend" : {
        "cause" : "Replication severely behind",
        "impact" : "If the nodes fails over, data will be missing on the replica. If you failover, information in the replication queue will be lost.",
        "action" : "Do not failover the node. Wait until replication queue is low to failover. If replication queue remains high, contact support@couchbase.com",
    },
    "DiskQueueDrainingAnalysis" :{
        "cause" : "Drain rate from RAM to disk is too slow; can be caused by disk fragmentation.",
        "impact" : "Rate of data persisted from RAM to disk is too high.",
        "action" : "Do not failover until drain rate is faster. Increase disk quota, add nodes to cluster, or remove and re-add a node. Please contact support@couchbase.com",
    },
}