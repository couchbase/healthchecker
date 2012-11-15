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
        'couch_docs_data_size' : {},
        'couch_docs_actual_disk_size' : {},
        'couch_total_disk_size' : {},
        'couch_docs_fragmentation' : {},
        'couch_views_actual_disk_size' : {},
        'couch_views_data_size' : {},
        'couch_views_fragmentation' : {},
        'couch_views_ops' : {},
        'curr_connections' : {},
        'curr_items' : {},
        'delete_hits' : {},
        'disk_write_queue' : {},
        'ep_bg_fetched' : {},
        'ep_cache_miss_rate' : {},
        'ep_num_ops_del_meta' : {},
        'ep_num_ops_get_meta' : {},
        'ep_num_ops_set_meta' : {},
        'ep_oom_errors' : {},
        'ep_tap_total_total_backlog_size' : {},
        'ep_tmp_oom_errors' : {},
        'mem_used' : {},
        'replication_changes_left' : {},
        'vb_active_num' : {},
        'vb_active_resident_items_ratio' : {},
        'vb_active_queue_drain' : {},
        'vb_replica_curr_items' : {},
        'vb_replica_num' : {},
        'vb_replica_resident_items_ratio' : {},
        'vb_replica_queue_drain' : {},
        'xdc_ops' : {},
}