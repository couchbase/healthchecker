TMP_DIR = ./tmp
TMP_VER = $(TMP_DIR)/version_num.tmp

PROJECT_NAME = cbhealthchecker

CHEETAH_LIB = ./Cheetah
COUCHBASE_CLI = ../couchbase-cli
CLI_PYTHON_LIB = $(COUCHBASE_CLI)/buckets.py \
                 $(COUCHBASE_CLI)/cb_bin_client.py \
                 $(COUCHBASE_CLI)/couchbaseConstants.py \
                 $(COUCHBASE_CLI)/info.py \
                 $(COUCHBASE_CLI)/listservers.py \
                 $(COUCHBASE_CLI)/restclient.py \
                 $(COUCHBASE_CLI)/simplejson \
                 $(COUCHBASE_CLI)/timeout.py \
                 $(COUCHBASE_CLI)/usage.py
default:

pythonlibdir=$(libdir)/python
pythonlib_DATA = \
    analyzer.py \
    bucket_stats.py \
    cluster_stats.py \
    collector.py \
    diskqueue_stats.py \
    node_stats.py \
    prescription.py \
    stats_buffer.py \
    threshold.py \
    util_cli.py

pythonlib_SCRIPTS= $(PROJECT_NAME)

PYTHON_TOOLS= wrapper/$(PROJECT_NAME)

${PYTHON_TOOLS}: wrapper/wrapper
	cp $< $@

CLEANFILES = ${PYTHON_TOOLS}
bin_SCRIPTS = ${PYTHON_TOOLS}

EXTRA_DIST = $(pythonlib_DATA) $(pythonlib_SCRIPTS) LICENSE

clean-local:
	rm -f membase*tar.gz
	rm -rf $(TMP_DIR)

install-data-hook:
	cp -rf $(CHEETAH_LIB) reports $(CLI_PYTHON_LIB) $(pythonlibdir)

bdist:
	test -d $(TMP_DIR) || mkdir $(TMP_DIR)
	git describe | sed s/-/_/g > $(TMP_VER)
	rm -f ./$(PROJECT_NAME)_*.tar.gz
	rm -rf $(TMP_DIR)/$(PROJECT_NAME)
	mkdir -p $(TMP_DIR)/$(PROJECT_NAME)
	cp $(PROJECT_NAME) *.py  $(TMP_DIR)/$(PROJECT_NAME)
	cp -rf $(CHEETAH_LIB) reports $(CLI_PYTHON_LIB) LICENSE $(TMP_DIR)/$(PROJECT_NAME)
	cp $(TMP_VER) $(TMP_DIR)/$(PROJECT_NAME)/VERSION.txt
	(cd $(TMP_DIR); tar cf - $(PROJECT_NAME)) | gzip -9 > $(PROJECT_NAME)-`cat $(TMP_VER)`.tar.gz
	rm -rf $(TMP_DIR)

