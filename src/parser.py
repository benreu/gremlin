# parser.py
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
UI_FILE = "src/parser.ui"

def create_arduino_file (textbuffer, file_):
	start = textbuffer.get_start_iter()
	end = textbuffer.get_end_iter()
	text = textbuffer.get_text(start, end, True)
	code = ''
	tabs = 0
	previous_tabs = 0
	start_braces = 0
	stop_braces = 0
	indents = 0
	text = text.split("\n")
	for line_number, line in enumerate (text):
		comment = line.find('//')
		if comment == -1:
			comment = None  #get the end of the line on uncommented lines
		tabs = line[0:comment].count("\t")
		if tabs > indents: #check for unexpected indents
			return ("Indentation error! please check your indentation\n"
					"on line %s." % (line_number + 1) )
		if ":" in line[0:comment]:
			if line.startswith(" "):
				return ("Syntax error! line starts with space\n"
						"on line %s." % (line_number + 1) )
			elif line.startswith("void "):
				tabs = 0
				line = line.replace(":", "{")
			elif line.startswith("int "):
				tabs = 0
				line = line.replace(":", "{")
			elif line.startswith("bool "):
				tabs = 0
				line = line.replace(":", "{")
			elif line.startswith("ISR "):
				tabs = 0
				line = line.replace(":", "{")
			elif "for " in line[0:comment] or "for(" in line[0:comment]:
				line = line.replace("for ", "for(")
				line = line.replace(":", ") {")
			elif "if " in line[0:comment] or "if(" in line[0:comment]:
				line = line.replace("if ", "if(")
				line = line.replace(":", ") {")
			elif "else " in line[0:comment] or "else:" in line[0:comment]:
				line = line.replace(":", "{")
			elif "while " in line[0:comment] or "while(" in line[0:comment]:
				line = line.replace("while ", "while(")
				line = line.replace(":", ") {")
			start_braces += 1
			indents += 1
		elif line[0:comment].strip("\t") != "" and "#" not in line[0:comment]:
			original_line = line  #find comments and deal with them by prepending ; before //
			line = original_line[:comment] + ";" 
			if '//' in original_line:
				line += original_line[comment:]
		for i in range(previous_tabs - tabs):# ending braces for the unindents
			if stop_braces < start_braces:
				new_line = ("\t" * previous_tabs) + "}\n"
				code += new_line
				stop_braces += 1
				indents -= 1
		code += line + "\n"
		previous_tabs = tabs
		
	start_braces = code.count ("{")
	stop_braces = code.count("}")
	for i in range (start_braces - stop_braces): #fixes problem of no proper unindenting at the end
		code += '}\n'
	f = open(file_, 'w')
	f.write (code)
	f.close ()
	return True

def view_code (file_):
	builder = Gtk.Builder()
	builder.add_from_file(UI_FILE)
	f = open(file_, 'r')
	code = f.read ()
	f.close ()
	builder.get_object('textbuffer1').set_text(code)
	window = builder.get_object('window1')
	window.show_all()

def code_window_delete (window, event):
	window.hide()
	return True


	
	
