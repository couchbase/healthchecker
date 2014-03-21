PROJECT(HealthChecker)
CMAKE_MINIMUM_REQUIRED(VERSION 2.8)

# Generate the python wrappers
CONFIGURE_FILE (${CMAKE_CURRENT_SOURCE_DIR}/wrapper/wrapper.in
                ${CMAKE_CURRENT_BINARY_DIR}/wrapper/cbhealthchecker)

INSTALL(PROGRAMS
        ${CMAKE_CURRENT_BINARY_DIR}/wrapper/cbhealthchecker
        DESTINATION bin)

INSTALL(PROGRAMS
        cbhealthchecker
        DESTINATION lib/python)

INSTALL(FILES
        analyzer.py
        bucket_stats.py
        cluster_stats.py
        collector.py
        dbaccessor.py
        diskqueue_stats.py
        node_map.py
        node_stats.py
        prescription.py
        stats_buffer.py
        threshold.py
        DESTINATION lib/python)


INSTALL(FILES
        Cheetah/__init__.py
        Cheetah/CacheRegion.py
        Cheetah/CacheStore.py
        Cheetah/CheetahWrapper.py
        Cheetah/Compiler.py
        Cheetah/convertTmplPathToModuleName.py
        Cheetah/DirectiveAnalyzer.py
        Cheetah/Django.py
        Cheetah/DummyTransaction.py
        Cheetah/ErrorCatchers.py
        Cheetah/FileUtils.py
        Cheetah/Filters.py
        Cheetah/ImportHooks.py
        Cheetah/ImportManager.py
        Cheetah/NameMapper.py
        Cheetah/Parser.py
        Cheetah/Servlet.py
        Cheetah/SettingsManager.py
        Cheetah/SourceReader.py
        Cheetah/Template.py
        Cheetah/TemplateCmdLineIface.py
        Cheetah/Unspecified.py
        Cheetah/Version.py
        DESTINATION lib/python/Cheetah)

INSTALL(FILES
        Cheetah/c/_filters.c
        Cheetah/c/_namemapper.c
        Cheetah/c/_template.c
        Cheetah/c/cheetah.h
        DESTINATION lib/python/Cheetah/c)

INSTALL(FILES
        Cheetah/Macros/__init__.py
        Cheetah/Macros/I18n.py
        DESTINATION lib/python/Cheetah/Macros)


INSTALL(FILES
        Cheetah/Templates/__init__.py
        Cheetah/Templates/_SkeletonPage.py
        Cheetah/Templates/SkeletonPage.py
        Cheetah/Templates/SkeletonPage.tmpl
        DESTINATION lib/python/Cheetah/Templates)

INSTALL(FILES
        Cheetah/Tests/__init__.py
        Cheetah/Tests/Analyzer.py
        Cheetah/Tests/CheetahWrapper.py
        Cheetah/Tests/Cheps.py
        Cheetah/Tests/Filters.py
        Cheetah/Tests/Misc.py
        Cheetah/Tests/NameMapper.py
        Cheetah/Tests/Parser.py
        Cheetah/Tests/Performance.py
        Cheetah/Tests/Regressions.py
        Cheetah/Tests/SyntaxAndOutput.py
        Cheetah/Tests/Template.py
        Cheetah/Tests/Test.py
        Cheetah/Tests/Unicode.py
        Cheetah/Tests/xmlrunner.py
        DESTINATION lib/python/Cheetah/Tests)

INSTALL(FILES
        Cheetah/Tools/__init__.py
        Cheetah/Tools/CGITemplate.py
        Cheetah/Tools/MondoReport.py
        Cheetah/Tools/MondoReportDoc.txt
        Cheetah/Tools/RecursiveNull.py
        Cheetah/Tools/SiteHierarchy.py
        DESTINATION lib/python/Cheetah/Tools)

INSTALL(FILES
        Cheetah/Tools/turbocheetah/__init__.py
        Cheetah/Tools/turbocheetah/cheetahsupport.py
        DESTINATION lib/python/Cheetah/Tools/turbocheetah)

INSTALL(FILES
        Cheetah/Tools/turbocheetah/tests/__init__.py
        Cheetah/Tools/turbocheetah/tests/test_template.py
        DESTINATION lib/python/Cheetah/Tools/turbocheetah/tests)

INSTALL(FILES
        Cheetah/Utils/__init__.py
        Cheetah/Utils/htmlDecode.py
        Cheetah/Utils/htmlEncode.py
        Cheetah/Utils/Indenter.py
        Cheetah/Utils/Misc.py
        Cheetah/Utils/statprof.py
        Cheetah/Utils/WebInputMixin.py
        DESTINATION lib/python/Cheetah/Utils)

INSTALL(FILES
        reports/chart.tmpl
        reports/template.tmpl
        DESTINATION lib/python/reports)


INSTALL(FILES
        reports/css/all.css
        reports/css/bootstrap-responsive.css
        reports/css/bootstrap.css
        reports/css/bootstrap.min.css
        reports/css/docs.css
        reports/css/nv.d3.css
        reports/css/print.css
        reports/css/screen.css
        DESTINATION lib/python/reports/css)

INSTALL(FILES
        reports/image/arrows.png
        reports/image/couchbase.png
        reports/image/glyphicons-halflings-white.png
        reports/image/glyphicons-halflings.png
        reports/image/header_bkg.png
        reports/image/icons.png
        reports/image/logo_for_print.png
        reports/image/logo_large.png
        reports/image/row_bkg.png
        DESTINATION lib/python/reports/image)

INSTALL(FILES
        reports/js/app.js
        reports/js/bootstrap.js
        reports/js/bootstrap.min.js
        reports/js/d3.v2.min.js
        reports/js/expandtable.js
        reports/js/jquery-2.0.2.min.js
        reports/js/jquery-2.0.3.min.js
        reports/js/line.js
        reports/js/lineChart.js
        reports/js/nv.d3.js
        reports/js/nv.d3.min.js
        reports/js/underscore.min.js
        reports/js/utils.js
        reports/js/zepto.min.js
        DESTINATION lib/python/reports/js)

# Do we really need this in bin??
INSTALL(FILES
        reports/chart.tmpl
        reports/template.tmpl
        DESTINATION bin/reports)


INSTALL(FILES
        reports/css/all.css
        reports/css/bootstrap-responsive.css
        reports/css/bootstrap.css
        reports/css/bootstrap.min.css
        reports/css/docs.css
        reports/css/nv.d3.css
        reports/css/print.css
        reports/css/screen.css
        DESTINATION bin/reports/css)

INSTALL(FILES
        reports/image/arrows.png
        reports/image/couchbase.png
        reports/image/glyphicons-halflings-white.png
        reports/image/glyphicons-halflings.png
        reports/image/header_bkg.png
        reports/image/icons.png
        reports/image/logo_for_print.png
        reports/image/logo_large.png
        reports/image/row_bkg.png
        DESTINATION bin/reports/image)

INSTALL(FILES
        reports/js/app.js
        reports/js/bootstrap.js
        reports/js/bootstrap.min.js
        reports/js/d3.v2.min.js
        reports/js/expandtable.js
        reports/js/jquery-2.0.2.min.js
        reports/js/jquery-2.0.3.min.js
        reports/js/line.js
        reports/js/lineChart.js
        reports/js/nv.d3.js
        reports/js/nv.d3.min.js
        reports/js/underscore.min.js
        reports/js/utils.js
        reports/js/zepto.min.js
        DESTINATION bin/reports/js)
