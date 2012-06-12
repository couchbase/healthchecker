TMP_DIR = ./tmp
TMP_VER = $(TMP_DIR)/version_num.tmp

PROJECT_NAME = healthchecker
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
    mc_bin_client.py \
    memcacheConstants.py \
    node_stats.py \
    restclient.py \
    stats_buffer.py \
    usage.py \
    util_cli.py \
    report-htm.tmpl

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
	cp -rf $(CHEETAH_LIB) $(JSON_LIB) $(pythonlibdir)

bdist:
	test -d $(TMP_DIR) || mkdir $(TMP_DIR)
	git describe | sed s/-/_/g > $(TMP_VER)
	rm -f ./$(PROJECT_NAME)_*.tar.gz
	rm -rf $(TMP_DIR)/$(PROJECT_NAME)
	mkdir -p $(TMP_DIR)/$(PROJECT_NAME)/simplejson
	cp $(PROJECT_NAME) *.py  $(TMP_DIR)/$(PROJECT_NAME)
	cp -rf $(CHEETAH_LIB) $(JSON_LIB) report-htm.tmpl LICENSE $(TMP_DIR)/$(PROJECT_NAME)
	(cd $(TMP_DIR); tar cf - $(PROJECT_NAME)) | gzip -9 > healtherChecker_`cat $(TMP_VER)`-`uname -s`.`uname -m`.tar.gz
	echo created healtherchecker_`cat $(TMP_VER)`-`uname -s`.`uname -m`.tar.gz
	rm -rf $(TMP_DIR)

