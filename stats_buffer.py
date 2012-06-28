nodes = {}
node_stats = {}

buckets_summary = {}
stats_summary = {}

bucket_info = {}
buckets = {}

stats = {
    "minute" : {},
    "hour" : {},
    "day" : {},
    "week" : {},
    "month" : {},
    "year" : {},
}

counters = {
        'cmd_get' : {},
        'cmd_set' : {},
        'curr_connections' : {},
        'curr_items' : {},
        'delete_hits' : {},
        'disk_write_queue' : {},
        'ep_cache_miss_rate' : {},
        'ep_oom_errors' : {},
        'ep_tap_total_total_backlog_size' : {},
        'ep_tmp_oom_errors' : {},
        'mem_used' : {},
        'vb_active_num' : {},
        'vb_active_resident_items_ratio' : {},
        'vb_active_queue_drain' : {},
        'vb_replica_curr_items' : {},
        'vb_replica_num' : {},
        'vb_replica_resident_items_ratio' : {},
        'vb_replica_queue_drain' : {},
}