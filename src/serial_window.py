# serial_window.py
#
# Copyright (C) 2017 - reuben
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


from gi.repository import Gtk, GObject, GLib
from multiprocessing import Queue, Process
from queue import Empty
from subprocess import Popen, PIPE, STDOUT
import serial

UI_FILE = "src/serial_window.ui"

class SerialWindowGUI:
	def __init__(self, parent):

		self.builder = Gtk.Builder()
		self.builder.add_from_file(UI_FILE)
		self.builder.connect_signals(self)
		self.parent = parent
		
		self.serial_buffer = self.builder.get_object('textbuffer1')
		self.serial_buffer.set_text('')
		self.timeout_id = None
		self.com_port = parent.com_port
		self.show_serial_monitor ()
		self.window = self.builder.get_object('serial_window')
		self.window.show_all()

	def present (self):
		self.window.present()

	def destroy (self):
		if self.timeout_id:
			GLib.source_remove(self.timeout_id)
			self.ser.close()
		self.parent.serial_instance = None
		self.window.destroy()
	
	def serial_window_delete_event (self, window, event): #window close button clicked
		self.destroy()

	def serial_baud_rate_combo_changed (self, combobox):
		if self.timeout_id:
			GLib.source_remove(self.timeout_id)
			self.ser.close()
		self.show_serial_monitor ()

	def flushInput (self):
		self.ser.flushInput ()

	def show_serial_monitor (self):
		baud_rate = self.builder.get_object('comboboxtext3').get_active_id()
		self.ser = serial.Serial(self.com_port, baud_rate)
		if self.ser.inWaiting () > 0:
			self.ser.flushInput ()
		self.timeout_id = GLib.timeout_add(10, self.retrieve_serial)
		self.builder.get_object('textview1').set_visible(True)

	def halt_serial_monitor (self):
		GLib.source_remove(self.timeout_id)
		self.serial_buffer.set_text('')
		self.builder.get_object('textview1').set_visible(False)
		
	def scroll_to_bottom (self):
		if self.builder.get_object('checkbutton1').get_active() == True:
			sw = self.builder.get_object('scrolledwindow3')
			adj = sw.get_vadjustment()
			adj.set_value(adj.get_upper() - adj.get_page_size())
		

	def retrieve_serial (self):
		while self.ser.inWaiting () > 0:
			bytes = self.ser.read(self.ser.inWaiting())
			text = bytes.decode(encoding="utf-8", errors="strict")
			end_iter = self.serial_buffer.get_end_iter()
			length = len(text)
			self.serial_buffer.insert (end_iter, text, length)
		GLib.idle_add (self.scroll_to_bottom)
		return True

		
