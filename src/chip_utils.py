# chip_utils.py
#
# Copyright (C) 2018 - reuben
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

from gi.repository import Gtk, GLib, Gdk, Vte
import xml.etree.ElementTree as xml
import configparser

UI_FILE = "src/chip_utils.ui"

class GUI:
	file_name = None
	populating = False
	clock_combo_changed = False
	
	def __init__(self, main ):

		self.work_dir = main.work_dir
		self.terminal = main.terminal
		self.main = main
		
		self.builder = Gtk.Builder()
		self.builder.add_from_file(UI_FILE)
		self.builder.connect_signals(self)

		self.window = self.builder.get_object('window1')
		self.window.show_all()
		self.load_main_cmd ()
		self.load_fuse_bit_descriptions()
		self.load_BOD_detection(connect = True)
		self.load_clock_selection (connect = True)



###########################  Clock to widgets config (unique per chip)



	def load_fuse_bit_descriptions (self):
		try:
			tree = xml.parse("AVR_fuses.xml")
			rootElement = tree.getroot()
			chips = rootElement.find('AVR_Fuses')
			for avr in chips.findall("AVR"):
				if avr.get('caption') == self.main.chip_name:
					for fuse in avr.findall('Fuse'):
						fbit = fuse.get('bit')
						fbyte = fuse.get('fuseByte')
						if fbyte == 'hfuse':
							cb=self.builder.get_object("hf"+fbit)
							cb.set_label(fuse.get('name'))
							cb.set_tooltip_text(fuse.get('desc'))
							cb.set_active(not int(fuse.get('default')))
						elif fbyte == 'lfuse':
							cb=self.builder.get_object("lf"+fbit)
							cb.set_label(fuse.get('name'))
							cb.set_tooltip_text(fuse.get('desc'))
							cb.set_active(not int(fuse.get('default')))
						elif fbyte == 'efuse':
							cb=self.builder.get_object("ef"+fbit)
							cb.set_label(fuse.get('name'))
							cb.set_tooltip_text(fuse.get('desc'))
							cb.set_active(not int(fuse.get('default')))
					break
			else:
				message = "Chip %s not found in xml file!" % self.main.chip_name 
				self.show_message (message)
				for bitnum in range(8):
					bn=str(bitnum)
					cb=self.builder.get_object("hf"+bn)	
					cb.set_label('bit '+bn)
					cb=self.builder.get_object("lf"+bn)	
					cb.set_label('bit '+bn)
					cb=self.builder.get_object("ef"+bn)	
					cb.set_label('bit '+bn)
		except Exception as e:
			self.show_message ('Error in xml fuse parsing: %s' % e)

	def load_clock_selection (self, widget = None, connect = False):
		if self.clock_combo_changed == True:
			return #feedback from the user selecting a combo setting
		clock_store = self.builder.get_object('clock_store')
		clock_store.clear()
		try:
			tree = xml.parse("AVR_fuses.xml")
			rootElement = tree.getroot()
			chips = rootElement.find('AVR_Fuses')
			for avr in chips.findall("AVR"):
				if avr.get('caption') == self.main.chip_name:
					CKlist = avr.find('ClockSelection')
					widgets = CKlist.find('Widgets')
					self.CKSEL0 = self.builder.get_object(widgets.get("CKSEL0widget"))
					self.CKSEL1 = self.builder.get_object(widgets.get("CKSEL1widget"))
					self.CKSEL2 = self.builder.get_object(widgets.get("CKSEL2widget"))
					self.CKSEL3 = self.builder.get_object(widgets.get("CKSEL3widget"))
					self.SUT0 = self.builder.get_object(widgets.get("SUT0widget"))
					self.SUT1 = self.builder.get_object(widgets.get("SUT1widget"))
					if connect == True:
						self.CKSEL0.connect('toggled', self.load_clock_selection)
						self.CKSEL1.connect('toggled', self.load_clock_selection)
						self.CKSEL2.connect('toggled', self.load_clock_selection)
						self.CKSEL3.connect('toggled', self.load_clock_selection)
						self.SUT0.connect('toggled', self.load_clock_selection)
						self.SUT1.connect('toggled', self.load_clock_selection)
					self.populating = True
					for CK in CKlist.findall('Setting'):
						clock_store.append([CK.get("bin"), CK.get('caption')])
						active = not self.CKSEL0.get_active()
						if int(active) != int(CK.get('Fuse1')):
							continue
						active = not self.CKSEL1.get_active()
						if int(active) != int(CK.get('Fuse2')):
							continue
						active = not self.CKSEL2.get_active()
						if int(active) != int(CK.get('Fuse3')):
							continue
						active = not self.CKSEL3.get_active()
						if int(active) != int(CK.get('Fuse4')):
							continue
						active = not self.SUT0.get_active()
						if int(active) != int(CK.get('Fuse5')):
							continue
						active = not self.SUT1.get_active()
						if int(active) != int(CK.get('Fuse6')):
							continue
						self.builder.get_object("clock_combo").set_active_id(CK.get("bin"))
					self.populating = False
					break
		except Exception as e:
			self.show_message ('Error in xml clock parsing: %s' % e)

	def load_BOD_detection (self, widget = None, connect = False):
		level_text = 'BOD setting not found!'
		try:
			tree = xml.parse("AVR_fuses.xml")
			rootElement = tree.getroot()
			fuses=rootElement.find('AVR_Fuses')
			for avr in fuses.findall("AVR"):
				if avr.get('caption') == self.main.chip_name:
					BODlist = avr.find('BrownOutDetection')
					widgets = BODlist.find('Widgets')
					widget0 = self.builder.get_object(widgets.get("BOD0widget"))
					widget1 = self.builder.get_object(widgets.get("BOD1widget"))
					widget2 = self.builder.get_object(widgets.get("BOD2widget"))
					if connect == True:
						widget0.connect('toggled', self.load_BOD_detection)
						widget1.connect('toggled', self.load_BOD_detection)
						widget2.connect('toggled', self.load_BOD_detection)
					for BOD in BODlist.findall('Setting'):
						active = not widget0.get_active()
						if int(active) != int(BOD.get('Fuse1')):
							continue
						active = not widget1.get_active()
						if int(active) != int(BOD.get('Fuse2')):
							continue
						active = not widget2.get_active()
						if int(active) != int(BOD.get('Fuse3')):
							continue
						level_text = BOD.get('caption')
						break
					break
			self.builder.get_object("bod_detection_label").set_label(level_text)
		except Exception as e:
			self.show_message ('Error in xml BOD parsing: %s' % e)

	def chip_clock_combo_changed (self, combo):
		config = combo.get_active_id()
		if self.populating == True or config == None:
			return
		self.clock_combo_changed = True
		self.CKSEL3.set_active(not bool(int(config[0])))
		self.CKSEL2.set_active(not bool(int(config[1])))
		self.CKSEL1.set_active(not bool(int(config[2])))
		self.CKSEL0.set_active(not bool(int(config[3])))
		self.SUT1.set_active(not bool(int(config[4])))
		self.SUT0.set_active(not bool(int(config[5])))
		self.clock_combo_changed = False

	def fuse_hex_checkbuttons_toggled (self, checkbutton):
		if self.populating == True:
			return
		fusebyte=0
		for bn in range(8):
			b=self.builder.get_object("ef"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		self.builder.get_object('efuse_entry').set_text('0x%02x' % fusebyte)
		fusebyte=0
		for bn in range(8):
			b=self.builder.get_object("lf"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		self.builder.get_object('lfuse_entry').set_text('0x%02x' % fusebyte)
		fusebyte=0
		for bn in range(8):
			b=self.builder.get_object("hf"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		self.builder.get_object('hfuse_entry').set_text('0x%02x' % fusebyte)
		fusebyte=0
		for bn in range(6):
			b=self.builder.get_object("lk"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		fusebyte += 192 # blank bits
		self.builder.get_object('lk_fuse_entry').set_text('0x%02x' % fusebyte)

	def lfuse_entry_activated (self, entry):
		try:
			text = hex(int(entry.get_text(), 16))
			entry.set_text(text)
			entry.override_color(Gtk.StateFlags.NORMAL, None)
		except ValueError as e:
			self.show_message(str(e))
			entry.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1,0,0,1))
			return
		for bp in range(8):
			cb=self.builder.get_object("lf"+str(bp))
			cb.set_active (not (int(text,16)&(1<<bp)))

	def hfuse_entry_activated (self, entry):
		try:
			text = hex(int(entry.get_text(), 16))
			entry.set_text(text)
			entry.override_color(Gtk.StateFlags.NORMAL, None)
		except ValueError as e:
			self.show_message(str(e))
			entry.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1,0,0,1))
			return
		for bp in range(8):
			cb=self.builder.get_object("hf"+str(bp))
			cb.set_active (not (int(text,16)&(1<<bp)))

	def efuse_entry_activated (self, entry):
		try:
			text = hex(int(entry.get_text(), 16))
			entry.set_text(text)
			entry.override_color(Gtk.StateFlags.NORMAL, None)
		except ValueError as e:
			self.show_message(str(e))
			entry.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1,0,0,1))
			return
		for bp in range(8):
			cb=self.builder.get_object("ef"+str(bp))
			cb.set_active (not (int(text,16)&(1<<bp)))

	def lo_fuse_entry_activated (self, entry):
		try:
			text = hex(int(entry.get_text(), 16))
			entry.set_text(text)
			entry.override_color(Gtk.StateFlags.NORMAL, None)
		except ValueError as e:
			self.show_message(str(e))
			entry.override_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(1,0,0,1))
			return
		for bp in range(6):
			cb=self.builder.get_object("lk"+str(bp))
			cb.set_active (not (int(text,16)&(1<<bp)))

########################  Project load/save and chip read/write

	def load_main_cmd(self):
		self.main_cmd = "/usr/bin/avrdude %s %s %s" % 	(self.main.chip_tag ,
														self.main.programmer, 
														self.main.protocol)

	def destroy_window (self, window):
		self.main.chip_utils = None

	def save_to_file_clicked (self, button):
		if self.file_name == None:
			self.save_as_file ()
		else:
			self.save_to_file()

	def save_as_file_clicked (self, button):
		self.save_as_file ()
		
	def save_as_file (self):
		dialog = self.builder.get_object('file_save_dialog')
		if self.file_name:
			dialog.set_filename(self.file_name)
		result = dialog.run()
		dialog.hide()
		if result != Gtk.ResponseType.ACCEPT:
			return
		self.file_name = dialog.get_filename()
		if not self.file_name.endswith(".gcp"):
			self.file_name += ".gcp"
		self.save_to_file()
		self.builder.get_object('filename_label').set_label(self.file_name)

	def load_from_file_clicked (self, button):
		dialog = self.builder.get_object('file_open_dialog')
		result = dialog.run()
		dialog.hide()
		if result != Gtk.ResponseType.ACCEPT:
			return
		self.file_name = dialog.get_filename()
		config = configparser.ConfigParser()
		try:
			config.read(self.file_name)
			flash = config.get("DATA", "flash")
			eeprom = config.get("DATA", "eeprom")
			low_fuse = hex(int(config.get("DATA", "low_fuse"), 16))
			high_fuse = hex(int(config.get("DATA", "high_fuse"), 16))
			ext_fuse = hex(int(config.get("DATA", "ext_fuse"), 16))
			lock_fuse = hex(int(config.get("DATA", "lock_fuse"), 16))
		except Exception as e:
			self.show_message(e)
			return
		self.builder.get_object('flash_buffer').set_text(flash)
		self.builder.get_object('eeprom_buffer').set_text(eeprom)
		self.builder.get_object('lfuse_entry').set_text(low_fuse)
		self.builder.get_object('hfuse_entry').set_text(high_fuse)
		self.builder.get_object('efuse_entry').set_text(ext_fuse)
		self.builder.get_object('lk_fuse_entry').set_text(lock_fuse)
		for bp in range(8):
			cb=self.builder.get_object("lf"+str(bp))
			cb.set_active(not (int(low_fuse,16)&(1<<bp)))
		for bp in range(8):
			cb=self.builder.get_object("hf"+str(bp))
			cb.set_active(not (int(high_fuse,16)&(1<<bp)))
		for bp in range(8):
			cb=self.builder.get_object("ef"+str(bp))
			cb.set_active(not (int(ext_fuse,16)&(1<<bp)))
		for bp in range(6):
			cb=self.builder.get_object("lk"+str(bp))
			cb.set_active(not (int(lock_fuse,16)&(1<<bp)))
		self.builder.get_object('filename_label').set_label(self.file_name)

	def get_hexcode_fom_flash_buffer (self):
		buf = self.builder.get_object('flash_buffer')
		start_iter = buf.get_start_iter()
		end_iter = buf.get_end_iter()
		return buf.get_text(start_iter, end_iter, True)

	def get_hexcode_fom_eeprom_buffer (self):
		buf = self.builder.get_object('eeprom_buffer')
		start_iter = buf.get_start_iter()
		end_iter = buf.get_end_iter()
		return buf.get_text(start_iter, end_iter, True)

	def save_to_file (self):
		low_fuse = self.builder.get_object('lfuse_entry').get_text()
		high_fuse = self.builder.get_object('hfuse_entry').get_text()
		ext_fuse = self.builder.get_object('efuse_entry').get_text()
		lock_fuse = self.builder.get_object('lk_fuse_entry').get_text()
		flash = self.get_hexcode_fom_flash_buffer()
		eeprom = self.get_hexcode_fom_eeprom_buffer()
		config = configparser.ConfigParser()
		if not config.has_section('DATA'):
			config.add_section('DATA')
		config.set("DATA", "flash", flash)
		config.set("DATA", "eeprom", eeprom)
		config.set("DATA", "low_fuse", str(low_fuse))
		config.set("DATA", "high_fuse", str(high_fuse))
		config.set("DATA", "ext_fuse", str(ext_fuse))
		config.set("DATA", "lock_fuse", str(lock_fuse))
		try:
			with open(self.file_name, 'w') as fp:
				config.write(fp)
		except Exception as e:
			self.show_message(e)

	def write_chip_project_clicked (self, button):
		self.terminal.reset(True, True)
		self.write_flash_to_temp_file ()
		cmd = '%s -U flash:w:%s/flash.hex:a' % (self.main_cmd, self.work_dir)
		self.write_eeprom_to_temp_file ()
		cmd += ' -U eeprom:w:%s/eeprom.hex:a' % self.work_dir
		cmd += self.get_fuses_cmd ()
		self.run(cmd)

	def read_chip_project_clicked (self, button):
		self.terminal.reset(True, True)
		cmd = self.main_cmd + ' -U flash:r:%s/flash.hex:i' % self.work_dir
		self.run(cmd)
		self.handler_id = self.terminal.connect("child-exited", self.read_flash, True)

	def read_flash_clicked (self, button):
		cmd = self.main_cmd + ' -U flash:r:%s/flash.hex:i' % self.work_dir
		self.run(cmd)
		self.handler_id = self.terminal.connect("child-exited", self.read_flash)
		
	def read_flash (self, terminal, result, project = False):
		terminal.disconnect(self.handler_id)
		if result != 0:
			self.show_message ("Read failed! Check output on main window.")
			self.main.window.present()
			return
		with open(self.work_dir+'/flash.hex','r') as fp:
			code = fp.read()
			self.builder.get_object('flash_buffer').set_text(code)
		if project == True:
			cmd = self.main_cmd + ' -U eeprom:r:%s/eeprom.hex:i' % self.work_dir
			self.run(cmd)
			self.handler_id = self.terminal.connect("child-exited", self.read_eeprom, project)

	def write_flash_to_temp_file (self):
		"write the flash in the GUI to work_dir/flash.hex"
		code = self.get_hexcode_fom_flash_buffer ()
		with open(self.work_dir + '/flash.hex', 'w') as fp: 
			fp.write(code)

	def write_flash_clicked (self, button):
		self.write_flash_to_temp_file ()
		cmd = '%s -U flash:w:%s/flash.hex:a' % (self.main_cmd, self.work_dir)
		self.run(cmd)
		self.handler_id = self.terminal.connect("child-exited", self.write_finished)

	def verify_flash_clicked (self, button):
		self.write_flash_to_temp_file ()
		cmd = '%s -U flash:v:%s/flash.hex:a' % (self.main_cmd, self.work_dir)
		self.run(cmd)
		self.handler_id = self.terminal.connect("child-exited", self.verify_finished)
		
	def verify_finished (self, terminal, result):
		terminal.disconnect(self.handler_id)
		if result != 0:
			self.show_message ("Verify failed! Check output on main window.")
			self.main.window.present()
		else:
			self.show_success()

	def verify_eeprom_clicked (self, button):
		self.write_eeprom_to_temp_file ()
		cmd = '%s -U eeprom:v:%s/eeprom.hex:a' % (self.main_cmd, self.work_dir)
		self.run(cmd)
		self.handler_id = self.terminal.connect("child-exited", self.verify_finished)

	def write_eeprom_to_temp_file (self):
		"write the flash in the GUI to work_dir/eeprom.hex"
		code = self.get_hexcode_fom_eeprom_buffer()
		with open(self.work_dir + '/eeprom.hex', 'w') as fp: 
			fp.write(code)

	def write_eeprom_clicked (self, button):
		self.write_eeprom_to_temp_file ()
		cmd = '%s -U eeprom:w:%s/eeprom.hex:a' % (self.main_cmd, self.work_dir)
		self.run(cmd)
		self.handler_id = self.terminal.connect("child-exited", self.write_finished)

	def read_eeprom_clicked (self, button):
		self.terminal.reset(True, True)
		cmd = self.main_cmd + ' -U eeprom:r:%s/eeprom.hex:i' % self.work_dir
		self.run(cmd)
		self.handler_id = self.terminal.connect("child-exited", self.read_eeprom)
		
	def read_eeprom (self, terminal, result, project = False):
		terminal.disconnect(self.handler_id)
		if result != 0:
			self.show_message ("Read failed! Check output on main window.")
			self.main.window.present()
			return
		with open(self.work_dir+'/eeprom.hex','r') as fp:
			code = fp.read()
			self.builder.get_object('eeprom_buffer').set_text(code)
		if project == True:
			self.read_fuses()

	def verify_fuses_clicked (self, button):
		self.terminal.reset(True, True)
		fusebyte=0
		for bn in range(8):
			b=self.builder.get_object("ef"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		cmd = ' -U efuse:v:0x%02x:m' % fusebyte
		fusebyte=0
		for bn in range(8):
			b=self.builder.get_object("lf"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		cmd += ' -U lfuse:v:0x%02x:m' % fusebyte
		fusebyte=0
		for bn in range(8):
			b=self.builder.get_object("hf"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		cmd += ' -U hfuse:v:0x%02x:m' % fusebyte
		fusebyte=0
		for bn in range(6):
			b=self.builder.get_object("lk"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		fusebyte += 192 # blank bits
		cmd += ' -U lock:v:0x%02x:m' % fusebyte
		self.run(self.main_cmd + cmd)
		self.handler_id = self.terminal.connect("child-exited", self.verify_fuses)
		
	def verify_fuses (self, terminal, result):
		terminal.disconnect(self.handler_id)
		if result != 0:
			self.show_message ("Verify failed! Check output on main window.")
			self.main.window.present()
		else:
			self.show_success()

	def read_fuses_clicked (self, button):
		self.terminal.reset(True, True)
		self.read_fuses()

	def read_fuses(self):
		cmd = "%s -U lfuse:r:%s/low.bin:h "\
				"-U hfuse:r:%s/high.bin:h "\
				"-U efuse:r:%s/ext.bin:h  "\
				"-U lock:r:%s/lock.bin:h " % (self.main_cmd, 
												self.work_dir, 
												self.work_dir, 
												self.work_dir, 
												self.work_dir)
		self.run(cmd)
		self.handler_id = self.terminal.connect("child-exited", self.show_fuses)
		
	def show_fuses (self, terminal, result):
		terminal.disconnect(self.handler_id)
		if result != 0:
			self.show_message ("Read failed! Check output on main window.")
			self.main.window.present()
			return
		with open(self.work_dir+'/low.bin','r') as fp:
			lf=fp.readline()
			self.builder.get_object('lfuse_entry').set_text(lf.strip('\n'))
			for bp in range(8):
				cb=self.builder.get_object("lf"+str(bp))
				cb.set_active(not (int(lf,16)&(1<<bp)))
		with open(self.work_dir+'/high.bin','r') as fp:
			hf=fp.readline()
			self.builder.get_object('hfuse_entry').set_text(hf.strip('\n'))
			for bp in range(8):
				cb=self.builder.get_object("hf"+str(bp))
				cb.set_active(not (int(hf,16)&(1<<bp)))
		with open(self.work_dir+'/ext.bin','r') as fp:
			ef=fp.readline()
			self.builder.get_object('efuse_entry').set_text(ef.strip('\n'))
			for bp in range(8):
				cb=self.builder.get_object("ef"+str(bp))
				cb.set_active(not (int(ef,16)&(1<<bp)))
		with open(self.work_dir+'/lock.bin','r') as fp:
			lock=fp.readline()
			self.builder.get_object('lk_fuse_entry').set_text(lock.strip('\n'))
			for bp in range(6):
				cb=self.builder.get_object("lk"+str(bp))
				cb.set_active (not (int(lock,16)&(1<<bp)))

	def write_fuses_clicked (self, button):
		self.terminal.reset(True, True)
		cmd = self.main_cmd + self.get_fuses_cmd()
		self.run(cmd)
		self.handler_id = self.terminal.connect("child-exited", self.write_finished)

	def get_fuses_cmd (self):
		fusebyte=0
		for bn in range(8):
			b=self.builder.get_object("ef"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		cmd = ' -U efuse:w:0x%02x:m' % fusebyte
		fusebyte=0
		for bn in range(8):
			b=self.builder.get_object("lf"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		cmd += ' -U lfuse:w:0x%02x:m' % fusebyte
		fusebyte=0
		for bn in range(8):
			b=self.builder.get_object("hf"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		cmd += ' -U hfuse:w:0x%02x:m' % fusebyte
		fusebyte=0
		for bn in range(6):
			b=self.builder.get_object("lk"+str(bn))
			fusebyte += int(not b.get_active())*pow(2,bn)
		fusebyte += 192 # blank bits
		cmd += ' -U lock:w:0x%02x:m' % fusebyte
		return cmd
		
	def write_finished (self, terminal, result):
		terminal.disconnect(self.handler_id)
		if result != 0:
			self.show_message ("Write failed! Check output on main window.")
			self.main.window.present()
		else:
			self.show_success()

	def show_success (self):
		dialog = Gtk.MessageDialog(self.window,
									0,
									Gtk.MessageType.INFO,
									Gtk.ButtonsType.CLOSE,
									"Success")
		GLib.timeout_add_seconds(1, dialog.destroy)
		dialog.run()

	def show_message (self, message):
		dialog = Gtk.MessageDialog(self.window,
									0,
									Gtk.MessageType.ERROR,
									Gtk.ButtonsType.CLOSE,
									str(message))
		dialog.run()
		dialog.destroy()

	def run (self, cmd):
		if self.builder.get_object('verbose_checkbutton').get_active():
			print (cmd)
		self.terminal.spawn_sync(
								Vte.PtyFlags.DEFAULT,
								self.work_dir,
								cmd.split(),
								[],
								GLib.SpawnFlags.DO_NOT_REAP_CHILD,
								None,
								None,
								)

	def erase_chip_clicked (self, button):
		dialog = Gtk.MessageDialog(self.window,
									0,
									Gtk.MessageType.QUESTION,
									Gtk.ButtonsType.NONE,
									"Chip erase!\nAre you sure?")
		dialog.add_button("Cancel", -6)
		dialog.add_button("Erase chip", -3)
		response = dialog.run()
		dialog.destroy()
		if response == Gtk.ResponseType.ACCEPT:
			self.run(self.main_cmd + " -e")

	def info_clicked (self, button):
		cmd = self.main_cmd + ' -t'
		self.run(cmd)
		self.terminal.feed_child('part\n', -1)
		self.terminal.feed_child('sig\n', -1)
		self.terminal.feed_child('d lfuse\n', -1)
		self.terminal.feed_child('d hfuse\n', -1)
		self.terminal.feed_child('d efuse\n', -1)
		self.terminal.feed_child('quit\n', -1)
		self.main.window.present()









