#!/usr/bin/env python3

import sys
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

def main():
    import gremlin
    gremlin.GUI()
    Gtk.main()
		
if __name__ == "__main__":
    sys.exit(main())
