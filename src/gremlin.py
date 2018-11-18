# gremlin.py
# Copyright (C) 2016 reuben
# 
# gremlin is free software: you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# gremlin is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License along
# with this program.  If not, see <http://www.gnu.org/licenses/>.
import gi
gi.require_version('Gtk', '3.0')
gi.require_version('GtkSource', '3.0')
gi.require_version('Vte', '2.91')
from gi.repository import Gtk, Gio, Gdk, GtkSource, GObject, GLib, Vte
import os, sys, subprocess, re, configparser, glob, shutil
from multiprocessing import Queue, Process
from queue import Empty
from subprocess import Popen, PIPE, STDOUT
from datetime import datetime
import serial
import parser, chip_utils

UI_FILE = "src/gremlin.ui"

class GUI:
	work_dir = None
	chip_utils = None
	terminal = None
	com_port = None
	serial_instance = None
	
	def __init__(self):

		self.builder = Gtk.Builder()
		GObject.type_register(GtkSource.View)
		self.builder.add_from_file(UI_FILE)
		self.builder.connect_signals(self)

		style_provider = Gtk.CssProvider()
		css = open('./custom.css', 'rb')
		css_data = css.read()
		css.close()

		style_provider.load_from_data(css_data)
		Gtk.StyleContext.add_provider_for_screen(
							Gdk.Screen.get_default(), 
							style_provider,
							Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION	)
		
		language_manager = GtkSource.LanguageManager()
		self.source_view = self.builder.get_object('gtksourceview1')
		self.source_buffer = GtkSource.Buffer()
		self.source_buffer.connect_after('changed', self.code_buffer_changed)
		self.source_view.set_buffer(self.source_buffer)
		self.source_buffer.set_language(language_manager.get_language('arduino'))
		completion = self.source_view.get_completion()
		keyword_provider = GtkSource.CompletionWords.new('Keywords')
		keyword_provider.register(self.source_buffer)
		completion.add_provider(keyword_provider) 

		self.search_context = GtkSource.SearchContext.new(self.source_buffer, None)
		self.search_settings = self.search_context.get_settings()
		self.search_settings.set_wrap_around (True)
		self.search_mark = Gtk.TextMark()

		self.window = self.builder.get_object('window')
		self.statusbar = self.builder.get_object('statusbar1')
		self.search_grid = self.builder.get_object('grid1')
		
		self.terminal = Vte.Terminal()
		self.ino = "/usr/local/lib/python2.7/dist-packages/ino-0.3.6-py2.7.egg/EGG-INFO/scripts/ino"
		self.terminal.set_scroll_on_output(True)
		self.builder.get_object('scrolledwindow2').add(self.terminal)
		self.builder.get_object('comboboxtext1').set_active(0)
		self.window.show_all()

		config = configparser.ConfigParser()
		config.read('./preferences.ini')
		self.path = config['paths']['remote']
		if not os.path.exists(self.path):
			self.path = config['paths']['local']
		path_string = "Arduino folder is %s" % self.path
		self.builder.get_object('label11').set_label(path_string)
		self.check_work_dir ()
		self.populate_sketch_menu()
		GLib.idle_add(self.populate_examples )
		
		self.passed_filename_check()
		self.load_code_from_file()
		
		sort = Gtk.SortType.ASCENDING
		self.builder.get_object('function_store').set_sort_column_id(1, sort)
		self.builder.get_object('radiomenuitem2').set_active(True)

	def find_entry_activated (self, entry):
		self.search_forward()

	def find_entry_search_changed (self, search_entry):
		search_text = search_entry.get_text()
		self.search_settings.set_search_text(search_text)
		self.search_mark = self.source_buffer.get_insert()
		self.search_forward ()

	def find_menuitem_activated (self, menuitem):
		self.search_grid.set_visible(True)
		self.builder.get_object('searchentry2').set_visible(False)
		self.builder.get_object('button15').set_visible(False)
		self.builder.get_object('button16').set_visible(False)
		result = self.source_buffer.get_selection_bounds()
		search_entry = self.builder.get_object('searchentry1')
		if len(result) == 2:
			start_iter, end_iter = result[0], result[1]
			search_text = self.source_buffer.get_text(start_iter, end_iter, True)
			# next line will trigger find_entry_search_changed 
			search_entry.set_text(search_text)
		search_entry.grab_focus()

	def find_and_replace_menuitem_activated (self, menuitem):
		result = self.source_buffer.get_selection_bounds()
		search_entry = self.builder.get_object('searchentry1')
		if len(result) == 2:
			start_iter, end_iter = result[0], result[1]
			search_text = self.source_buffer.get_text(start_iter, end_iter, True)
			# next line will trigger find_entry_search_changed 
			search_entry.set_text(search_text)
		self.search_grid.set_visible(True)
		self.builder.get_object('searchentry2').set_visible(True)
		self.builder.get_object('button15').set_visible(True)
		self.builder.get_object('button16').set_visible(True)

	def find_forward_button_clicked (self, button):
		self.search_forward ()

	def search_forward (self):
		search_iter = self.source_buffer.get_iter_at_mark (self.search_mark)
		search_iter.forward_char()    #advance the search by one char
		result = self.search_context.forward(search_iter)
		valid, start_iter, end_iter = result[0], result[1], result[2]
		if valid == True:
			self.source_buffer.move_mark(self.search_mark, end_iter)
			self.source_buffer.select_range(start_iter, end_iter)
			self.source_view.scroll_to_iter(end_iter, 0.1, True, 0.0, 0.5)

	def find_backward_button_clicked (self, button):
		search_iter = self.source_buffer.get_iter_at_mark (self.search_mark)
		result = self.search_context.backward(search_iter)
		valid, start_iter, end_iter = result[0], result[1], result[2]
		if valid == True: 
			self.source_buffer.move_mark(self.search_mark, start_iter)
			self.source_buffer.select_range(start_iter, end_iter)
			self.source_view.scroll_to_iter(start_iter, 0.1, True, 0.0, 0.5)

	def find_replace_button_clicked (self, button):
		result = self.source_buffer.get_selection_bounds()
		if len(result) == 2 :
			start_iter, end_iter = result[0], result[1]
			replace = self.builder.get_object('searchentry2').get_text()
			length = len(replace)
			self.source_buffer.move_mark(self.search_mark, end_iter)
			self.search_context.replace(start_iter, end_iter, replace, length)
			self.search_forward()

	def find_replace_all_button_clicked (self, button):
		result = self.source_buffer.get_selection_bounds()
		if len(result) == 2 :
			start_iter, end_iter = result[0], result[1]
			replace = self.builder.get_object('searchentry2').get_text()
			length = len(replace)
			self.source_buffer.move_mark(self.search_mark, end_iter)
			self.search_context.replace_all(replace, length)

	def line_number_entry_activated (self, entry, icon = None, event = None):
		line = entry.get_text()
		if line != '':
			line_number = int(line) - 1
			text_iter = self.source_buffer.get_iter_at_line (line_number)
			self.source_buffer.place_cursor(text_iter)
			self.source_view.scroll_to_iter(text_iter, 0.1, True, 0.0, 0.5)

	def find_close_button_clicked (self, button):
		self.search_grid.set_visible(False)

	def preferences_activated (self, menuitem):
		return
		import preferences
		preferences.PreferencesGUI(self)

	def serial_monitor_button_clicked (self, button):
		if not self.com_port:
			self.statusbar.pop(1)
			self.statusbar.push(1, 'No serial port selected!')
			self.populate_ports ()
			menu = self.builder.get_object('menu4')
			menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
			menu.show_all()
			return
		if not self.serial_instance:
			import serial_window
			self.serial_instance = serial_window.SerialWindowGUI(self)
		else:
			self.serial_instance.present()
	
	def populate_ports (self): #ripped off from gnoduino
		menu = self.builder.get_object('menu4')
		for i in menu.get_children():
				menu.remove(i)
		tryports = glob.glob('/dev/ttyS*') + \
					glob.glob('/dev/ttyUSB*') + \
					glob.glob('/dev/ttyACM*')
		menu_item = Gtk.MenuItem.new_with_label("Select port")
		menu_item.set_sensitive(False)
		menu_item.show()
		menu.append(menu_item)
		for i in tryports:
			try:
				s = serial.Serial(i)
				menu_item = Gtk.MenuItem.new_with_label(label = s.portstr)
				menu_item.connect('activate', 
								self.serial_port_menuitem_activated, 
								s.portstr)
				menu_item.show()
				menu.append(menu_item)
				s.close()
			except serial.SerialException:
				pass

	def alphabetical_radiobutton_toggled (self, radiobutton):
		if radiobutton.get_active():
			self.builder.get_object('treeviewcolumn1').set_sort_column_id (0)
			self.builder.get_object('function_store').set_sort_column_id(0, 
														Gtk.SortType.ASCENDING)

	def line_number_radiobutton_toggled (self, radiobutton):
		if radiobutton.get_active():
			self.builder.get_object('treeviewcolumn1').set_sort_column_id (1)
			self.builder.get_object('function_store').set_sort_column_id(1, 
														Gtk.SortType.ASCENDING)

	def serial_port_menuitem_activated(self, menuitem, port):
		self.com_port = port
		if self.serial_instance:
			self.serial_instance.destroy()
		self.builder.get_object('label9').set_label(port)

	def passed_filename_check(self):
		try:
			self.filename = sys.argv[1]
		except:
			self.filename = "./untitled.gremlin"

	def compile_clicked (self, button):
		self.compile_code()

	def upload_clicked (self, button):
		if not self.com_port:
			self.statusbar.pop(1)
			self.statusbar.push(1, 'No serial port selected!')
			self.populate_ports ()
			menu = self.builder.get_object('menu4')
			menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())
			menu.show_all()
			return
		if self.code_compiled == False:
			self.compile_code(upload = True)
		else:
			self.terminal.reset(True, True)
			self.upload ()

	def view_parsed_code_activated (self, button):
		if self.builder.get_object('radiobutton1').get_active() == True:
			return #block parsing native C syntax
		file_location = "%s/src/sketch.ino" % self.work_dir
		result = parser.create_arduino_file (self.source_buffer, file_location)
		if result != True:
			self.show_message (result)
			return
		parser.view_code(file_location)
		
	def combo1_changed(self, combo):
		if self.work_dir and os.path.exists(self.work_dir):
			shutil.rmtree(self.work_dir)
		self.board_tag = combo.get_active_text()
		self.chip_name = combo.get_active_id()
		self.chip_tag = '-p' + self.chip_name
		if self.chip_utils:
			self.chip_utils.window.destroy()
			self.chip_utils = chip_utils.GUI(self)
		self.check_work_dir() 
		self.code_compiled = False

	def ispmkii_toggled (self, checkmenuitem):
		if checkmenuitem.get_active() == True:
			self.builder.get_object('menuitem14').set_label('Programmer (AVRISP mkII)')
			self.programmer = "-cstk500v2"
			self.protocol = "-Pusb"
			if self.chip_utils:
				self.chip_utils.load_main_cmd()

	def usbtinyisp_toggled (self, checkmenuitem):
		if checkmenuitem.get_active() == True:
			self.builder.get_object('menuitem14').set_label('Programmer (USBtinyISP)')
			self.programmer = "-cusbtiny"
			self.protocol = ""
			if self.chip_utils:
				self.chip_utils.load_main_cmd()

	def chip_utils_activated (self, menuitem = None):
		if self.chip_utils:
			self.chip_utils.window.present()
		else: 
			self.chip_utils = chip_utils.GUI(self)

	def port_menu_button_clicked (self, menubutton):
		if menubutton.get_active():
			self.populate_ports()

	def export_compiled_hex_activated (self, menuitem):
		from pathlib import Path
		p = Path(self.work_dir)
		for i in p.glob(".build/**/firmware.hex"):
			hex_file = i
			break
		else:
			raise Exception ("firmware.hex not found in .build/*/, aborting")
		print (hex_file)

	def upload_using_programmer_activated (self, menuitem):
		if self.code_compiled == False:
			self.compile_code(upload_using_programmer = True)
		else:
			self.terminal.reset(True, True)
			self.upload_using_programmer ()

	def upload_using_programmer (self):
		from pathlib import Path
		p = Path(self.work_dir)
		for i in p.glob(".build/**/firmware.hex"):
			hex_file = "-Uflash:w:%s:i" % i
			break
		else:
			raise Exception ("firmware.hex not found in .build/*/, aborting upload")
		self.terminal.spawn_sync(
								Vte.PtyFlags.DEFAULT,
								self.work_dir,
								["/usr/bin/avrdude", self.chip_tag, self.programmer, self.protocol, hex_file],
								[],
								GLib.SpawnFlags.DO_NOT_REAP_CHILD,
								None,
								None,
								)

	def upload (self):
		self.statusbar.pop(1)
		self.statusbar.push(1, 'Uploading ...')
		if self.serial_instance:
			self.serial_instance.halt_serial_monitor ()
		self.terminal.spawn_sync(
								Vte.PtyFlags.DEFAULT,
								self.work_dir,
								[self.ino, "upload", "-p", self.com_port, "-m", self.board_tag, "-d", self.path],
								[],
								GLib.SpawnFlags.DO_NOT_REAP_CHILD,
								None,
								None,
								)
		self.handler_id = self.terminal.connect("child-exited", self.upload_callback)
	
	def compile_code(self, upload = False, upload_using_programmer = False):
		if self.builder.get_object('checkbutton1').get_active () == False:
			self.file_save ()
		file_location = "%s/src/sketch.ino" % self.work_dir
		if self.builder.get_object('radiobutton1').get_active() == True:
			#compile native C
			start = self.source_buffer.get_start_iter()
			end = self.source_buffer.get_end_iter()
			text = self.source_buffer.get_text(start, end, True)
			f = open(file_location, 'w')
			f.write (text)
			f.close ()
		else:
			result = parser.create_arduino_file (self.source_buffer, 
															file_location)
			if result != True:
				self.show_message (result)
				return
		self.statusbar.pop(1)
		self.statusbar.push(1, 'Compiling ...')
		self.terminal.reset(True, True)
		self.terminal.spawn_sync(
								Vte.PtyFlags.DEFAULT,
								self.work_dir,
								[self.ino, "build", "-m", self.board_tag, "-d", self.path],
								[],
								GLib.SpawnFlags.DO_NOT_REAP_CHILD,
								None,
								None,
								)
		self.handler_id = self.terminal.connect("child-exited", self.compile_callback, upload, upload_using_programmer)
		self.code_compiled = True

	def compile_callback (self, terminal, error, upload, upload_using_programmer):
		terminal.disconnect(self.handler_id)
		if error == 0 and upload == True:
			self.upload ()
		elif error == 0 and upload_using_programmer == True:
			self.upload_using_programmer ()
		elif error != 0:
			self.statusbar.pop(1)
			self.statusbar.push(1, 'Compile failed!')

	def upload_callback(self, terminal, error):
		terminal.disconnect(self.handler_id)
		self.statusbar.pop(1)
		text = terminal.get_text()[0]
		if "have given up" in text or "Double check chip" in text\
									or "attempt 10 of 10" in text:
			self.statusbar.push(1, 'Upload failed!')
		else:
			self.statusbar.push(1, 'Successful')
		if self.serial_instance:
			self.serial_instance.show_serial_monitor ()

	def new_activated (self, menuitem):
		subprocess.Popen("./src/main.py")

	def file_open (self, menuitem):
		file_open = self.builder.get_object('filechooserdialog1')	#File > Open 
		file_open.select_filename(self.filename)
		result = file_open.run()
		if result == Gtk.ResponseType.ACCEPT:
			file_ = file_open.get_filename()
			subprocess.Popen(["./src/main.py", file_])
		file_open.hide()

	def load_code_from_file (self):
		if self.filename.endswith('.gremlin') == True:
			self.builder.get_object('radiobutton2').set_active(True)
		else:
			self.builder.get_object('radiobutton1').set_active(True)
		self.source_buffer.begin_not_undoable_action()
		try:
			with open(self.filename,"r") as f:
				code = f.read()
		except Exception as e:
			self.show_message (e)
			return
		self.source_buffer.set_text(code)
		self.source_buffer.end_not_undoable_action()
		self.source_buffer.set_modified(False)
		self.populate_function_store ()
		final_name = (self.filename.split('/'))[-1:][0]
		self.window.set_title( "%s Gremlin" % final_name)

	def file_save (self, menuitem = None):					#File > Save
		if self.filename == ("./untitled.gremlin"):
			self.file_save_as ()
		else:
			self.save_to_file()

	def check_work_dir(self):
		work_dir = '/tmp/inotool%s' % datetime.today()
		self.work_dir = re.sub(" ", "_", work_dir)
		os.mkdir(self.work_dir)
		try :
			self.terminal.spawn_sync(
									Vte.PtyFlags.DEFAULT,
									self.work_dir,
									[self.ino, "init"],
									[],
									GLib.SpawnFlags.DO_NOT_REAP_CHILD,
									None,
									None
									)
		except Exception as e:
			self.show_message(str(e))
		self.statusbar.pop(1)
		self.statusbar.push(1, 'Ino init...')
		
	def file_save_as (self, menuitem = None):
		file_save_as = self.builder.get_object('filechooserdialog2')	#File > Save As
		file_save_as.select_filename(self.filename)
		file_save_as.set_keep_above(True)
		result = file_save_as.run()
		if result == Gtk.ResponseType.ACCEPT:
			self.filename = file_save_as.get_filename()
			self.save_to_file()
		file_save_as.hide()

	def save_to_file(self):
		code = self.source_buffer.get_text(self.source_buffer.get_start_iter(), 
											self.source_buffer.get_end_iter(),
											True)  #True is for hidden characters
		try:
			with open(self.filename,"w") as f:
				f.write(code)
		except Exception as e:
			self.show_message(e)
			return
		final_name = (self.filename.split('/'))[-1:][0]
		self.window.set_title( "%s Gremlin" % final_name) #should be OK to do this in "Save As" but ...
		self.statusbar.pop(1)
		self.statusbar.push(1, 'Done saving')
		self.source_buffer.set_modified(False)
		self.populate_function_store ()

	def code_buffer_changed (self, buffer_):
		self.code_compiled = False
		final_name = (self.filename.split('/'))[-1:][0]
		if self.source_buffer.get_modified():
			self.window.set_title( "*%s Gremlin" % final_name)

	def on_key_press(self, view, event):
		"""Check if the key press is 'Return' or 'Backspace' and indent or
		un-indent accordingly. """
		key_name = Gdk.keyval_name(event.keyval)
		if key_name not in ('Return', 'Backspace') or \
			len(self.source_buffer.get_selection_bounds()) != 0:
			# If some text is selected we want the default behavior of Return
			# and Backspace so we do nothing
			return

		if view.get_insert_spaces_instead_of_tabs():
			self.indent = ' ' * view.props.tab_width
		else:
			self.indent = '\t'

		if key_name == 'Return':
			line = self._get_current_line(self.source_buffer)

			if line.endswith(':'):
				old_indent = line[:len(line) - len(line.lstrip())]
				self.source_buffer.insert_at_cursor('\n' + old_indent + self.indent)
				return True

			else:
				stripped_line = line.strip()
				n = len(line) - len(line.lstrip())
				if (stripped_line.startswith('return')
				or stripped_line.startswith('break')
				or stripped_line.startswith('continue')
				or stripped_line.startswith('pass')):
					n -= len(self.indent)

					self.source_buffer.insert_at_cursor('\n' + line[:n])
					self._scroll_to_cursor(self.source_buffer, view)
					return True

		if key_name == 'BackSpace':
			line = self._get_current_line(self.source_buffer)

			if line.strip() == '' and line != '':
				length = len(self.indent)
				nb_to_delete = len(line) % length or length
				self._delete_before_cursor(self.source_buffer, nb_to_delete)
				self._scroll_to_cursor(self.source_buffer, view)
				return True

	def _get_current_line(self, buffer):
		iter_cursor = self._get_iter_cursor(buffer)
		iter_line = buffer.get_iter_at_line(iter_cursor.get_line())
		return buffer.get_text(iter_line, iter_cursor, False)

	def _get_current_line_nb(self, buffer):
		iter_cursor = self._get_iter_cursor(buffer)
		return iter_cursor.get_line()

	def _get_iter_cursor(self, buffer):
		cursor_position = buffer.get_property('cursor-position')
		return buffer.get_iter_at_offset(cursor_position)

	def _scroll_to_cursor(self, buffer, view):
		lineno = self._get_current_line_nb(buffer) + 1
		insert = buffer.get_insert()
		view.scroll_mark_onscreen(insert)

	def populate_function_store (self):
		store = self.builder.get_object('function_store')
		store.clear()
		start_iter = self.source_buffer.get_start_iter()
		end_iter = self.source_buffer.get_end_iter()
		text = self.source_buffer.get_text(start_iter, end_iter, True)
		for index, row in enumerate(text.split('\n')):
			comment = row.find('//')
			if row[0:1] != '\t' and row[0:1] != ' ' and ':' in row:
				function = row.split()[1]
				store.append([function, index])

	def function_row_activated (self, treeview, path, treeview_column):
		store = treeview.get_model()
		function_row = store[path][1]
		text_iter = self.source_buffer.get_iter_at_line (function_row)
		self.source_buffer.place_cursor(text_iter)
		self.source_view.scroll_to_iter(text_iter, 0.1, True, 0.0, 0.5)

	def view_log_activated (self, menuitem):
		import view_log
		view_log.ViewLogGUI()

	def quit_activated (self, menuitem):
		self.delete_event()

	def recent_chooser_activated (self, recent_chooser):
		file_ = recent_chooser.get_current_uri()
		file_ = file_.replace('%20', ' ').replace('file://', '')
		subprocess.Popen(["./src/main.py", file_])

	def functions_toggled (self, check_menuitem):
		function_widget = self.builder.get_object('box6')
		visible = check_menuitem.get_active()
		function_widget.set_visible (visible)

	def delete_event (self, window, event = None):
		if self.source_buffer.get_modified():
			unsaved_dialog = self.builder.get_object('unsaved_dialog')
			response = unsaved_dialog.run()
			unsaved_dialog.hide()
			if response == Gtk.ResponseType.ACCEPT:
				self.file_save()
				if self.source_buffer.get_modified(): # save operation may have failed
					return True
			elif response == Gtk.ResponseType.CANCEL:
				return True #block closing the main window
		shutil.rmtree(self.work_dir)
		Gtk.main_quit()

	def populate_examples (self):
		menu = self.builder.get_object('menu6')
		top_level = '%s/examples/'% self.path
		if not os.path.exists(top_level):
			print ("No examples directory > %s" % top_level)
			return
		for i in sorted(os.listdir(top_level)):
			examples = os.path.join(top_level,i)
			if os.path.isdir(examples):
				child_menuitem = Gtk.MenuItem(i)
				menu.add(child_menuitem)
				new_menu = Gtk.Menu()
				child_menuitem.set_submenu(new_menu)
				for entry in os.scandir(examples): 
					self.scan_example_directory(new_menu, entry)
		menu.show_all()

	def scan_example_directory (self, menu, object_):
		if object_.is_dir():
			child_menuitem = Gtk.MenuItem(object_.name)
			menu.add(child_menuitem)
			new_menu = Gtk.Menu()
			child_menuitem.set_submenu(new_menu)
			for entry in os.scandir(object_.path):
				self.scan_example_directory(new_menu, entry)
		elif object_.is_file():
			file_name = object_.name
			#file_name = file_name.rstrip('.gremlin')
			menuitem = Gtk.MenuItem(label = file_name)
			menu.add(menuitem)
			menuitem.connect('activate', self.open_gremlin_with_file, object_.path)

	def populate_sketch_menu (self):
		menu = self.builder.get_object('menu5')
		for file_ in glob.glob('%s/*.*'% self.path):
			file_name = file_.split('/')[-1:][0]
			file_name = file_name.rstrip('.gremlin')
			menuitem = Gtk.MenuItem(label = file_name)
			menu.add(menuitem)
			menuitem.show()
			menuitem.connect('activate', self.open_gremlin_with_file, file_)

	def open_gremlin_with_file (self, menuitem, file_):
		subprocess.Popen(["./src/gremlin.py", file_])

	def about_activated (self, menuitem):
		dialog = self.builder.get_object('aboutdialog1')
		dialog.run()
		dialog.hide()

	def show_message (self, message):
		dialog = Gtk.MessageDialog(self.window,
									0,
									Gtk.MessageType.ERROR,
									Gtk.ButtonsType.CLOSE,
									str(message))
		dialog.run()
		dialog.destroy()


