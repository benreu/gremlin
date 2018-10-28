# preferences.py
#
# Copyright (C) 2017 - reuben
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

from gi.repository import Gtk
import configparser

UI_FILE = "src/preferences.ui"

class PreferencesGUI:
	def __init__ (self, parent):

		self.builder = Gtk.Builder()
		self.builder.add_from_file(UI_FILE)
		self.builder.connect_signals(self)
		
		self.parent = parent
		config = configparser.ConfigParser()
		config.read('./preferences.ini')
		local = config['paths']['local']
		remote = config['paths']['remote']
		self.builder.get_object('radiobutton1').set_label(local)
		self.builder.get_object('radiobutton2').set_label(remote)

		self.window = self.builder.get_object('window')
		self.window.show_all()

	def remote_radiobutton_toggled (self, radiobutton):
		local = self.builder.get_object('radiobutton1').get_label()
		remote = self.builder.get_object('radiobutton2').get_label()
		if radiobutton.get_active():
			cmd = "cp -r %s/* %s\n" % (remote, local)
			length = len(cmd)
			self.parent.terminal.feed_child(cmd, length)
			self.parent.statusbar.pop(1)
			self.parent.statusbar.push(1, 'Copying files to local folder...')
		self.builder.get_object('label4').set_visible(True)








