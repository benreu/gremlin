## Process this file with automake to produce Makefile.in
## Created by Anjuta


uidir = $(pkgdatadir)/ui
ui_DATA = gremlin.ui \
	view_log.ui \
	serial_window.ui \
	parser.ui \
	preferences.ui \
	chip_utils.ui


## The main script
bin_SCRIPTS = gremlin.py

## Directory where .class files will be installed
gremlindir = $(pythondir)/gremlin


gremlin_PYTHON = \
	parser.py \
	view_log.py \
	gnoduino.png \
	serial_window.py \
	preferences.py \
	gremlin.py \
	main.py \
	chip_utils.py


EXTRA_DIST = $(ui_DATA)


# Remove ui directory on uninstall
uninstall-local:

	-rm -r $(uidir)

	-rm -r $(pkgdatadir)
