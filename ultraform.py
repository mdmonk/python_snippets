#!/usr/bin/env python

import sys
import os
import cgi
import cgitb; cgitb.enable()

from types import ListType

import formatter
import sgmllib

class dumb:
	def __init__(self):
		self.stupid = 1
		self.smart = 0

def hasPostData():
	return os.environ.get("REQUEST_METHOD",'') == "POST" and 0 < int(os.environ.get("CONTENT_LENGTH",0))

def format_tag(tag, attrs):
	if attrs:
		text_attrs = []
		for key,value in attrs:
			text_attrs.append( '%s="%s"' % (key,value) )
			
		sys.stdout.write("<%s %s>" % (tag, ' '.join(text_attrs)))
	else:
		sys.stdout.write("<%s>" % tag)


class UltraFormParser(sgmllib.SGMLParser):
	def __init__(self):
		"Create an ULTRAFORM parser."
		sgmllib.SGMLParser.__init__(self,formatter.NullFormatter())
		
		self.tag_dispatch = {
			't': self.deal_with_ultra,
			}
		
		self.ultra_dispatch = {
			'text': self.deal_text,
			'checkbox': self.deal_checkbox,
			'list': self.deal_list,
			'submit': self.deal_submit,
			}
		
	def process(self, data):
		"Process the given data and close."
		self.feed(data)
		self.close()
		
	def data_bind(self, namespace):
		"Set the namespace that data-bound controls will pull from."
		self.data_namespace = namespace

	def handle_data(self, data):
		"Output non-tag data."
		sys.stdout.write(data)

	def unknown_starttag(self, tag, attrs):
		"Output non-ULTRA tags, pass on ULTRA tags."
		name_parts = tag.split('.',1)
 		if len(name_parts) == 2:
 			func = self.tag_dispatch.get(name_parts[0])
 			if func:
				func(name_parts[1], dict(attrs))
			else:
				format_tag(tag, attrs)
 		else:
			format_tag(tag, attrs)

	def unknown_endtag(self, tag):
		"Output end tags."
		sys.stdout.write("</%s>" % tag)
	
	def deal_text(self, tag, attrs):
		global isPost

		tag_name = attrs.get('name', '')
		tag_value = ""
		if tag_name:
			if isPost:
				tag_value = form.getvalue(tag_name, "")
			else:
				bound_expr = attrs.get('bind')
				if bound_expr:
					try:
						tag_value = eval(bound_expr, self.data_namespace)
					except:
						tag_value = "#BIND ERROR#"
				else:
					tag_value = attrs.get('value', '')

		sys.stdout.write('<input type="text" name="%s" value="%s">' % (tag_name, tag_value))

	
	def deal_checkbox(self, tag, attrs):
		global isPost

		tag_name = attrs.get('name', '')
		tag_value = attrs.get('value','')
		
		tag_checked = ''
		if isPost:
			if tag_name in form:
#			if form.has_key(tag_name):
				tag_checked = ' checked'
		else:
			bound_expr = attrs.get('bind')
			if bound_expr:
				try:
					result = eval(bound_expr, self.data_namespace)
					if result:
						tag_checked = ' checked'
				except:
					# On bind error default to no check.
					pass
			else:
				if attrs.get('checked'):
					tag_checked = ' checked'
			
		sys.stdout.write('<input type="checkbox" name="%s" value="%s"%s>' % (tag_name, tag_value, tag_checked))
	
	def deal_submit(self, tag, attrs):
		global isPost
		
		tag_name = attrs.get('name', '')
		tag_value = attrs.get('caption','')
		
		attr_value = ""
		if tag_value:
			attr_value = ' value="%s"' % tag_value
		
		sys.stdout.write('<input type="submit" name="%s"%s>' % (tag_name, attr_value))


	def deal_list_checkbox(self, tag, attrs):
		global isPost

		tag_name = attrs.get('name', '')
		
		if isPost:
			tag_value = form.getvalue(tag_name)
			if not isinstance(tag_value, ListType):
				tag_value = [tag_value]
		else:
			tag_value = [attrs.get('value', '')]
			
		bind_list = attrs.get('bind-list')
		
		tag_list = []
		try:
			tag_list = eval(bind_list, self.data_namespace)
		except:
			tag_list.append( ('','#BIND ERROR#') )
		
		for value, name in tag_list:
			tag_checked = ""
			if value in tag_value:
				tag_checked = " checked"

			sys.stdout.write('<input type="checkbox" name="%(tag_name)s" value="%(value)s"%(tag_checked)s>%(name)s<br>\n' % vars())

	def deal_list_radio(self, tag, attrs):
		global isPost

		tag_name = attrs.get('name', '')
		
		if isPost:
			tag_value = form.getvalue(tag_name)
		else:
			tag_value = attrs.get('value', '')
			
		bind_list = attrs.get('bind-list')
		
		tag_list = []
		try:
			tag_list = eval(bind_list, self.data_namespace)
		except:
			tag_list.append( ('','#BIND ERROR#') )
		
		for value, name in tag_list:
			tag_checked = ""
			if tag_value == value:
				tag_checked = " checked"

			sys.stdout.write('<input type="radio" name="%(tag_name)s" value="%(value)s"%(tag_checked)s>%(name)s<br>\n' % vars())

	def deal_list_dropdown(self, tag, attrs):
		global isPost
		
		tag_name = attrs.get('name', '')
		
		if isPost:
			tag_value = form.getvalue(tag_name)
		else:
			tag_value = attrs.get('value', '')
			
		bind_list = attrs.get('bind-list')
		
		tag_list = []
		try:
			tag_list = eval(bind_list, self.data_namespace)
		except:
			tag_list.append( ('','#BIND ERROR#') )
		
		sys.stdout.write('<select name="%s">' % tag_name)
		for value, name in tag_list:
			tag_selected = ""
			if tag_value == value:
				tag_selected = " selected"

			sys.stdout.write('<option value="%(value)s"%(tag_selected)s>%(name)s\n' % vars())
		sys.stdout.write('</select>')

	def deal_list(self, tag, attrs):
		list_type = attrs.get('type', 'dropdown')
		
		if list_type == 'dropdown':
			self.deal_list_dropdown(tag, attrs)
		elif list_type == 'checkbox':
			self.deal_list_checkbox(tag, attrs)
		elif list_type == 'radio':		
			self.deal_list_radio(tag, attrs)
		
		
	def deal_with_ultra(self, tag, attrs):
		"Handle ULTRA tags"
		func = self.ultra_dispatch.get(tag)
		if func:
			func(tag, attrs)
		else:
			print "\t%s, %s<br>" % (tag, attrs)
		

def display_source():
	print "Content-type: text/plain\n"
	f = open("ultraform.py")
	print f.read()
	f.close()


def main():
	global form
	global isPost
	global ultraform
	
	form = cgi.FieldStorage()
	isPost = hasPostData()

	if form.getvalue("viewsource"):
		display_source();
		sys.exit(0)
		
	genders = (('n', 'None of your business'), ('m', 'Male'), ('f', 'Female'), ('t', 'Toilet Fixture'))

	print "Content-type: text/html\n"
	
	p = UltraFormParser()
	
	o = dumb()
	p.data_bind({'thing': 'This is the thing value.', 'user': o, 'genders': genders})
	
	p.process(ultraform)

# Sample page
ultraform = """
<html>
<head>
<title>Ultraform demo</title>
</head>

<body>
<form action="ultraform.py" method="post">
<table>
<tr>
	<td align="right">
	<b>Name:</b>
	</td>
	
	<td>
	<t.text name="name" value="Adam">
	</td>
</tr>

<tr>
	<td align="right">
	<b>Stuff:</b>
	</td>
	
	<td>
	<t.text name="stuff" bind="thing">
	</td>
</tr>

<tr>
	<td align="right">
	<b>Option:</b>
	</td>
	
	<td>
	<t.checkbox name="option3" value="some-value" checked="1"> On by default
	<br>
	<t.checkbox name="option4" value="another-value" bind="user.stupid"> Stupid?
	<br>
	<t.checkbox name="option5" value="another-value" bind="user.smart"> Smart?
	</td>
</tr>

<tr>
	<td align="right"><b>Gender:</b></td>
	<td>
	<t.list type="dropdown" name="gender" bind-list="genders" value="m">
	</td>
</tr>

<tr>
	<td align="right"><b>Gender:</b></td>
	<td>
	<t.list type="checkbox" name="gender2" bind-list="genders" value="m">
	</td>
</tr>

<tr>
	<td align="right"><b>Gender:</b></td>
	<td>
	<t.list type="radio" name="gender3" bind-list="genders" value="m">
	</td>
</tr>

<tr>
	<td></td>
	<td><t.submit caption="Do this thing."></td>
</tr>
</table>
</form>

<br>

<a href="ultraform.py">Back to default</a><br>
<a href="ultraform.py?viewsource=1">View source</a><br>

<hr>

<a href="../ultraform/">Back to projects</a><br>

</body>
</html>
"""

main()

