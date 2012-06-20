#!/usr/bin/python
# -*- coding: utf-8 -*-

ClusterCapsule = {
    "CacheMissRatio" :  2,
    "ActiveReplicaResidentRatio" : {
        "activeReplicaResidentRatio" : 1,
        "activeResidentRatio" : 30,
        "replicaResidentRatio" : 20,
    },
    "VBucketNumber" : {
        "activeVbucketNumber" : 1024,
        "replicaVBucketNumber" : 1024,
    },
    "RebalancePerformance" : {
        "highBackfillRemaing" : 1000,
        "tapNack" : 5,
    },
    "MemoryFragmentation" : {
        "totalFragmentation" : 1073741824, 
        "diskDelete" : 1000,
        "diskUpdate" : 1000,
        "diskInsert" : 1000,
        "diskCommit" : 5000000,
    },
    "EPEnginePerformance" : {
        "flusherState" : "running",
        "flusherCompleted" : 0,
        "avgItemLoadTime" : 100,
        "avgItemWaitTime" : 100,
    },
}

NodeCapsule = {
    "NumberOfConnection" : 1000,
    "checkpointPerformance" : 1000,
}

DiskQueueCapsule = {
    "DiskQueueDiagnosis" : {
        "avgDiskQueueLength" : {
                "low" : 50000000,
                "high" : 1000000000
            },
        "diskQueueTrend" : {
                "low" : 0.01,
                "high" : 0.25
            },
    },
    "ReplicationTrend" : {
        "percentage" : {
            "low" : 10.0,
            "high" : 30.0,
        },
        "number" : {
            "low" : 50000,
            "high" : 100000,
        },
    },
    "DiskQueueDrainingAnalysis" : {
        "activeDiskQueueDrainRate" : {
            "drainRate" : 0,
            "diskLength" : 100000,
        },
        "replicaDiskQueueDrainRate" : {
            "drainRate" : 0,
            "diskLength" : 100000,
        },
    },
}

