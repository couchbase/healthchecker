#!/usr/bin/python
# -*- coding: utf-8 -*-

ClusterCapsule = {
    "CacheMissRatio" :  2,
    "ActiveReplicaResidentRatio" : {
        "activeReplicaResidentRatio" : 4,
        "activeResidentRatio" : 30,
        "replicaResidentRatio" : 20,
    },
    "VBucketNumber" : {
        "activeVbucketNumber" : 1024,
        "replicaVBucketNumber" : 1024,
    },
    "RebalancePerformance" : {
        "highBackfillRemaing" : 10000,
        "tapNack" : 500,
    },
    "MemoryFragmentation" : {
        "totalFragmentation" : {
                "low" : 1073741824, # 1GB
                "high" : 2147483648, # 2GB
            },
        "diskDelete" : {
                "low" : 1000, #1ms
                "high" : 5000,
            },
        "diskUpdate" : {
                "low" : 1000, #1ms
                "high" : 5000,
            },
        "diskInsert" : {
                "low" : 1000, #1ms
                "high" : 5000,
            },
        "diskCommit" : {
                "low" : 5000000,
                "high" : 10000000,
            },
    },
    "EPEnginePerformance" : {
        "flusherState" : "running",
        "flusherCompleted" : 0,
        "avgItemLoadTime" : {
                "low" : 100,
                "high" : 500,
            },
        "avgItemWaitTime" : {
                "low" : 100,
                "high" : 500,
            },
    },
}

NodeCapsule = {
    "NumberOfConnection" : 1000,
    "checkpointPerformance" : 1000,
}

DiskQueueCapsule = {
    "DiskQueueDiagnosis" : {
        "avgDiskQueueLength" : {
                "low" : 500000,
                "high" : 1000000
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

