TMP_DIR = ./tmp
TMP_VER = $(TMP_DIR)/version_num.tmp

PROJECT_NAME = cbhealthchecker
CHEETAH_LIB = ./Cheetah
JSON_LIB = ./simplejson

default:

pythonlibdir=$(libdir)/python
pythonlib_DATA = \
    analyzer.py \
    bucket_stats.py \
    buckets.py \
    cluster_stats.py \
    collector.py \
    diskqueue_stats.py \
    info.py \
    listservers.py \
    cb_bin_client.py \
    couchbaseConstants.py \
    node_stats.py \
    prescription.py \
    restclient.py \
    stats_buffer.py \
    threshold.py \
    usage.py \
    util_cli.py \
    report-htm.tmpl

pythonlib_SCRIPTS= $(PROJECT_NAME)

PYTHON_TOOLS= wrapper/$(PROJECT_NAME)

${PYTHON_TOOLS}: wrapper/wrapper
	cp $< $@

CLEANFILES = ${PYTHON_TOOLS}
bin_SCRIPTS = ${PYTHON_TOOLS}

EXTRA_DIST = $(pythonlib_DATA) $(pythonlib_SCRIPTS) reports LICENSE

clean-local:
	rm -f membase*tar.gz
	rm -rf $(TMP_DIR)

install-data-hook:
	cp -rf $(CHEETAH_LIB) $(JSON_LIB) $(pythonlibdir)

bdist:
	test -d $(TMP_DIR) || mkdir $(TMP_DIR)
	git describe | sed s/-/_/g > $(TMP_VER)
	rm -f ./$(PROJECT_NAME)_*.tar.gz
	rm -rf $(TMP_DIR)/$(PROJECT_NAME)
	mkdir -p $(TMP_DIR)/$(PROJECT_NAME)/simplejson
	cp $(PROJECT_NAME) *.py  $(TMP_DIR)/$(PROJECT_NAME)
	cp -rf $(CHEETAH_LIB) $(JSON_LIB) reports LICENSE $(TMP_DIR)/$(PROJECT_NAME)
	cp $(TMP_VER) $(TMP_DIR)/$(PROJECT_NAME)/VERSION.txt
	(cd $(TMP_DIR); tar cf - $(PROJECT_NAME)) | gzip -9 > $(PROJECT_NAME)-`cat $(TMP_VER)`.tar.gz
	rm -rf $(TMP_DIR)

