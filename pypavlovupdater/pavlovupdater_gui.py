import pavlovupdater
import settings_manager

import sys
import logging
from datetime import datetime
import os
import io

import PySimpleGUI as sg
from PIL import Image
import requests


major_vers = 1
minor_vers = 4

### a few sets of functions to minimize the amount of API calls ###
# globally defined full pavlov mod array 
full_mods = None
# function to update modlist
def update_full_mods(pvu):
	global full_mods
	full_mods = pvu.get_pavlov_modlist()
	if 'error' in full_mods:
		if '401' in full_mods:
			logger.error('Error 401 when getting all mods, API key rejected')
			sg.Popup('Could not get all mods, API key was rejected', non_blocking=True, keep_on_top =True)
		else:
			logger.error(f'Error when getting all mods: {full_mods.strip("error")}')
			sg.Popup(f'Could not get all mods, Error {full_mods.strip("error")}', non_blocking=True, keep_on_top =True)
		full_mods = None
# function to get modlist without defining global
def get_full_mods(pvu):
	global full_mods
	if full_mods == None:
		update_full_mods(pvu)
	return full_mods
# get the entry of a mod by passing the ugc 'id' of the expected mod
def retrieve_full_mod_by_ugc(pvu, ugc):
	global full_mods
	if full_mods == None:
		update_full_mods(pvu)
	for entry in full_mods:
		if entry['id'] == ugc:
			return entry
	return None

# globally defined subscribed mod array 
subscribed_mods = None
# function to update modlist
def update_subscribed_mods(pvu):
	global subscribed_mods
	subscribed_mods = pvu.get_subscribed_modlist()
	if 'error' in subscribed_mods:
		if '401' in subscribed_mods:
			logger.error('Error 401 when getting subscribed mods, API key rejected')
			sg.Popup('Could not get subscribed mods, API key was rejected', non_blocking=True, keep_on_top =True)
		else:
			logger.error(f'Error when getting subscribed mods: {subscribed_mods.strip("error")}')
			sg.Popup(f'Could not get subscribed mods, Error {subscribed_mods.strip("error")}', non_blocking=True, keep_on_top =True)
		subscribed_mods = None
# function to get modlist without defining global
def get_subscribed_mods(pvu):
	global subscribed_mods
	if subscribed_mods == None:
		update_subscribed_mods(pvu)
	return subscribed_mods
# get the entry of a mod by passing the ugc 'id' of the expected mod
def retrieve_subscribed_mod_by_ugc(pvu, ugc):
	global subscribed_mods
	if subscribed_mods == None:
		update_subscribed_mods(pvu)
	for entry in subscribed_mods:
		if entry['id'] == ugc:
			return entry
	return None

# globally defined insatlled mod array 
installed_mods = None
# function to update modlist
def update_installed_mods(pvu):
	global installed_mods
	installed_mods = pvu.get_installed_modlist()
	if len(installed_mods) == 0:
		logger.error('No installed mods found')
		sg.Popup('Could not find installed mods, check that mod directory is valid. Disregard if intentional.', non_blocking=True, keep_on_top =True)
# function to get modlist without defining global
def get_installed_mods(pvu):
	global installed_mods
	if installed_mods == None:
		update_installed_mods(pvu)
	return installed_mods

# globally defined user rating dict 
user_ratings = None
# function to update modlist
def update_user_ratings(pvu):
	global user_ratings
	user_ratings = pvu.get_modio_user_ratings()
# function to get modlist without defining global
def get_user_ratings(pvu):
	global user_ratings
	if user_ratings == None:
		update_user_ratings(pvu)
	return user_ratings
# function to look for a user rating, defaults to 0
def get_user_rating_by_ugc(pvu, ugc):
	global user_ratings
	if user_ratings == None:
		update_user_ratings(pvu)
	if ugc in user_ratings:
		return user_ratings[ugc]
	return 0

# globally defined miscompare array vars
miscompares = None
not_installed = None
not_subscribed = None
# function to update modlists
def update_miscompares(pvu):
	global miscompares, not_installed, not_subscribed
	subbed = get_subscribed_mods(pvu)
	inst = get_installed_mods(pvu)
	if subbed == None or inst == None:
		return None, None, None
	# if len(not_installed) != 0 and 
	miscompares, not_installed, not_subscribed = pvu.find_miscompares_in_modlists(subbed, inst, printout=False)
# function to get modlists without defining global
def get_miscompares(pvu):
	global miscompares, not_installed, not_subscribed
	if miscompares == None:
		update_miscompares(pvu)
	return miscompares, not_installed, not_subscribed


### GUI functions ###
popup_title = 'PyPavlovUpdater Popup'
# global dict to hold created images (so they dont have to get loaded again)
image_bios = {}
download_popup_occured = False
def load_modio_image(pvu, modid, logo_url):
	global image_bios, download_popup_occured
	# make locals folder to store mod thumbnails
	if not os.path.exists('local'):
		os.mkdir('local')
	# check if the image has already been loaded
	if str(modid) not in image_bios:
		# make an address, check if it exists
		logo_faddr = f'local/UGC{modid}_logo.png'
		if not os.path.exists(logo_faddr):
			if not download_popup_occured:
				download_popup_occured = True
				sg.Popup('Downloading image thumbnails, this may take a bit', non_blocking = True, keep_on_top = True, title = 'Settings Error')

			try:
				# download an image and write it to faddr
				image_bin = pvu.get_modio_image(logo_url)
				with open(logo_faddr, 'wb') as f:
					f.write(image_bin)
			except Exception as e:
				# default to a pysimplegui emoji
				logger.exception(f'Exception when making mod item frame')
				logo_faddr = sg.EMOJI_BASE64_HAPPY_THUMBS_UP

		# resize the image and load it into the global dict
		image = Image.open(logo_faddr)
		image.thumbnail((200, 200))
		bio = io.BytesIO()
		image.save(bio, format="PNG")

		image_bios[str(modid)] = bio

		return bio
	else:
		return image_bios[str(modid)]

# like/dislike button colors
actv_green = ('white', 'green')
actv_red = ('white', 'red')
default_btn = ('white', '#082567')
# define the layout for mod lists
def make_mod_item_frame(pvu, mod, subbed_menu=True):
	
	image = load_modio_image(pvu, mod['id'], mod['logo'])

	user_mod_rating = get_user_rating_by_ugc(pvu, mod['id'])

	# make timestamp for last updated text
	date_str = datetime.fromtimestamp(mod['date_updated'])

	# image on the left
	col_left = [
		[sg.Image(data=image.getvalue())]
	]
	# mod information next to the image
	if subbed_menu:
		col_mid = [
			[sg.Text(f"{mod['name']:50s}")],
			[sg.Text(f"By {mod['maker']}")],
			[sg.Text(f"Version: {mod['modfile']['version']}")],
			[sg.Text(f"Last Updated {date_str}")],
			[sg.Text(f"Type {mod['type']}")],
		]
	else:
		col_mid = [
			[sg.Text(f"{mod['name']:50s}")],
			[sg.Text(f"By {mod['maker']}")],
			[sg.Text(f"Last Updated {date_str}")],
			[sg.Text(f"Type {mod['type']}")],
		]
	# mod options on the right
	subbed_status = True if retrieve_subscribed_mod_by_ugc(pvu, mod['id']) != None else False
	col_right = [
		[sg.Button('UnSub', key=f'__button_unsub_{mod["id"]}__', visible=subbed_status, expand_x=True)],
		[sg.Button('Sub', key=f'__button_sub_{mod["id"]}__', visible=(not subbed_status), expand_x=True)],
		[sg.Button('Like' if user_mod_rating <= 0 else 'Liked', key=f'__button_like_{mod["id"]}__', button_color=None if user_mod_rating <= 0 else actv_green, expand_x=True)],
		[sg.Button('Dislike' if user_mod_rating >= 0 else 'Disliked', key=f'__button_dislike_{mod["id"]}__', button_color=None if user_mod_rating >= 0 else actv_red, expand_x=True)],
	]

	# lay out columns of above elements to go in frame
	conts = [
		[sg.Column(col_left), sg.Column(col_mid,element_justification='left', expand_x=True), sg.Column(col_right, element_justification='right')],
		# [sg.Text(mod['description'])],
	]

	# return the assembled frame
	return sg.Frame(f"UGC{mod['id']}", conts, expand_x=True, pad=(0,5))

mods_per_page = 50

# define layout for the subscribed tab
def make_sub_mod_window(pvu, page=1, mod_filter=None, filter_type=None):
	# update user ratings 
	ratings = update_user_ratings(pvu)

	# get list of subscribed mods
	mods = get_subscribed_mods(pvu)
	if mods == None:
		return sg.Window(f'Subscribed Mods', [[sg.Text('Could not get subscribed mod list')]], finalize=True, size=(350,75))

	# if there is a mod filter, trim the mod list before beginning pagination
	if mod_filter != None:
		filtered_mods = []
		for mod in mods:
			# continue if mod filter input is not in the mod attribute
			if filter_type == 'Name':
				if mod_filter.lower() not in mod['name'].lower():
					continue
			if filter_type == 'Author':
				if mod_filter.lower() not in mod['maker'].lower():
					continue
			if filter_type == 'UGC':
				if mod_filter.lower() not in str(mod['id']):
					continue
			filtered_mods.append(mod)

		# replace local mod list
		mods = filtered_mods
		

	# calculate the number of pages based on mods_per_page, clean the input of values greater than max page
	num_mod_pages = int(len(mods)/mods_per_page)+1
	if page > num_mod_pages:
		page = num_mod_pages
	# get mod array index where the page starts
	mod_page_ind = (page-1)*mods_per_page
	# calculate the mod array offset
	mods_page_ind_offset = mods_per_page if len(mods) > (mods_per_page+mod_page_ind) else (len(mods)-mod_page_ind)
	# reduce mod list to the paginated mods
	mods = mods[mod_page_ind:mod_page_ind+mods_per_page]
	# get list of installed mods
	installed_mods = get_installed_mods(pvu)

	# find mods that are 1) not latest version, 2) not installed, 3) installed but not subscribed
	miscompares, not_installed, not_subscribed = get_miscompares(pvu)

	# make all of the mods into mod_item_layout items
	mods_left = []
	mods_right = []
	count = 1
	for mod in mods:			
		if count%2 == True:
			mods_left.append([make_mod_item_frame(pvu, mod, subbed_menu=True)])
		else:
			mods_right.append([make_mod_item_frame(pvu, mod, subbed_menu=True)])
		count += 1

	# reset global popup flag (need a better way to do this, only needed because of paginated icon downloads)
	global download_popup_occured
	download_popup_occured = False

	# assemble the layout into an array
	mods_layout_arr = [[sg.Column(mods_left, key='__subbed_mods_left__', vertical_alignment='top'), sg.Column(mods_right, key='__subbed_mods_right__', vertical_alignment='top')]]

	# filter modlist and make sure filter elements have an expected fallback value for display
	filter_modlist = ['Name','UGC','Author']
	filter_type = filter_type if filter_type != None else filter_modlist[0]
	mod_filter = mod_filter if mod_filter != None else ''

	button_line = [
		sg.Text('Filter'), 
		sg.Combo(filter_modlist, default_value=filter_type, key='__subbed_filttype__'), 
		sg.Input(mod_filter, key='__subbed_filter__', expand_x=True), 
		sg.Button('Submit', key='__button_subbed_filter__', bind_return_key=True),
		sg.Button('< Page', key='__button_subbed_page<__'),
		sg.Input(str(page), key='__subbed_page_num__', size=(3,0)), 
		sg.Text(f'of {str(num_mod_pages)}'), 
		sg.Button('Page >', key='__button_subbed_page>__'),
		]

	# make the larger subscribed mod window layout with the newly assembled mod layout
	assembled_layout = [
		[sg.Text(f'{len(mods)-len(miscompares)-len(not_installed)}/{len(mods)} Up to Date, {len(miscompares)} Out of Date, {len(not_installed)} Not Installed, {len(not_subscribed)} Not Subscribed'),
			sg.Column([[]], expand_x=True), 
			sg.Button(f'Subscribe to nonsubscribed-but-installed mods [{len(not_subscribed)}]', key='__button_subto_installed__'),
			sg.Button('Refresh Modlist', key='__button_subbed_refresh__'),],
		[sg.HorizontalSeparator()],
		button_line,
		[sg.Column(mods_layout_arr, key='__sub_mod_scrollable__', scrollable=True, justification='right', expand_x=True, expand_y=True)]#vertical_scroll_only=True,
	]

	# return the assembled window
	return sg.Window(f'Subscribed Mods', assembled_layout, size=(1300,500), resizable=True, finalize=True)


# define layout for the all-mod tab
def make_all_mod_window(pvu, page=1, mod_filter=None, filter_type=None):
	# update user ratings 
	ratings = update_user_ratings(pvu)

	# get list of subscribed mods
	mods = get_full_mods(pvu)
	if mods == None:
		return sg.Window(f'All Mods', [[sg.Text('Could not get full mod list')]], finalize=True, size=(350,75))

	# if there is a mod filter, trim the mod list before beginning pagination
	if mod_filter != None:
		filtered_mods = []
		for mod in mods:
			# continue if mod filter input is not in the mod attribute
			if filter_type == 'Name':
				if mod_filter.lower() not in mod['name'].lower():
					continue
			if filter_type == 'Author':
				if mod_filter.lower() not in mod['maker'].lower():
					continue
			if filter_type == 'UGC':
				if mod_filter.lower() not in str(mod['id']):
					continue
			filtered_mods.append(mod)

		# replace local mod list
		mods = filtered_mods
		

	# calculate the number of pages based on mods_per_page, clean the input of values greater than max page
	num_mod_pages = int(len(mods)/mods_per_page)+1
	if page > num_mod_pages:
		page = num_mod_pages
	# get mod array index where the page starts
	mod_page_ind = (page-1)*mods_per_page
	# calculate the mod array offset
	mods_page_ind_offset = mods_per_page if len(mods) > (mods_per_page+mod_page_ind) else (len(mods)-mod_page_ind)
	# reduce mod list to the paginated mods
	mods = mods[mod_page_ind:mod_page_ind+mods_per_page]
	# get list of installed mods
	installed_mods = get_installed_mods(pvu)

	# make all of the mods into mod_item_layout items
	mods_left = []
	mods_right = []
	count = 1
	for mod in mods:			
		if count%2 == True:
			mods_left.append([make_mod_item_frame(pvu, mod, subbed_menu=False)])
		else:
			mods_right.append([make_mod_item_frame(pvu, mod, subbed_menu=False)])
		count += 1

	# reset global popup flag (need a better way to do this, only needed because of paginated icon downloads)
	global download_popup_occured
	download_popup_occured = False

	# assemble the layout into an array
	mods_layout_arr = [[sg.Column(mods_left, key='__all_mod_mods_left__', vertical_alignment='top'), sg.Column(mods_right, key='__all_mod_mods_right__', vertical_alignment='top')]]

	# filter modlist and make sure filter elements have an expected fallback value for display
	filter_modlist = ['Name','UGC','Author']
	filter_type = filter_type if filter_type != None else filter_modlist[0]
	mod_filter = mod_filter if mod_filter != None else ''

	button_line = [
		sg.Text('Filter'), 
		sg.Combo(filter_modlist, default_value=filter_type, key='__all_mod_filttype__'), 
		sg.Input(mod_filter, key='__all_mod_filter__', expand_x=True), 
		sg.Button('Submit', key='__button_all_mod_filter__', bind_return_key=True),
		sg.Button('< Page', key='__button_all_mod_page<__'),
		sg.Input(str(page), key='__all_mod_page_num__', size=(3,0)), 
		sg.Text(f'of {str(num_mod_pages)}'), 
		sg.Button('Page >', key='__button_all_mod_page>__'),
		]

	# make the larger subscribed mod window layout with the newly assembled mod layout
	assembled_layout = [
		[sg.Column([[]], expand_x=True), sg.Button('Refresh Modlist', key='__button_all_mod_refresh__'),],
		[sg.HorizontalSeparator()],
		button_line,
		[sg.Column(mods_layout_arr, key='__all_mod_scrollable__', scrollable=True, justification='right', expand_x=True, expand_y=True)]#vertical_scroll_only=True,
	]

	# return the assembled window
	return sg.Window(f'All Mods', assembled_layout, size=(1300,500), resizable=True, finalize=True)


# define layout for downloads menu
def make_download_window(pvu):
	# get subscribed mods
	subbed_mods = get_subscribed_mods(pvu)
	if subbed_mods == None:
		return sg.Window(f'Download Menu', [[sg.Text('Could not open download menu')]], finalize=True, size=(350,75))
		
	# get list of installed mods
	installed_mods = get_installed_mods(pvu)

	# find mods that are 1) not latest version, 2) not installed, 3) installed but not subscribed
	miscompares, not_installed, not_subscribed = get_miscompares(pvu)

	# define a lot of arrays that will be columns
	ugc_col = ['UGC']
	modfile_id = ['ModfileID']
	name_col = ['Name']
	author_col = ['Author']
	size_col = ['Download Size (kb)']

	# start to fill those arrays with mod data
	for mod in miscompares:
		ugc_col.append(mod['id'])
		modfile_id.append(mod['modfile']['id'])
		name_col.append(mod['name'])
		author_col.append(mod['maker'])
		size_col.append(round(mod['modfile']['filesize']/1024, 1))

	for mod in not_installed:
		ugc_col.append(mod['id'])
		modfile_id.append(mod['modfile']['id'])
		name_col.append(mod['name'])
		author_col.append(mod['maker'])
		size_col.append(round(mod['modfile']['filesize']/1024, 1))

	# make a mod array into a formatted column of Text() objects
	def make_column(mod_texts, expand_x=False):
		new = []
		for text in mod_texts:
			new.append([sg.Text(text, expand_x=expand_x)])
		return sg.Column(new)
	
	# layout the checkbox column (with formatted keys for event/value handling)
	checkbox_col_layout = [[sg.Text('Download?', pad=(10,1))]]
	for i, ugc in enumerate(ugc_col):
		# hack so the array can be used for table headers
		if i==0:
			continue
		k = f'__cbox_download_UGC{ugc}_{modfile_id[i]}__'
		checkbox_col_layout.append([sg.CBox('', key=k, pad=(10,0.5))])
	
	# start the larger download menu assembly
	assembled_layout = [
		[sg.Text(f'{len(subbed_mods)-len(miscompares)-len(not_installed)}/{len(subbed_mods)} Up to Date, {len(miscompares)} Out of Date, {len(not_installed)} Not Installed'),
			sg.Column([[]], expand_x=True), 
			sg.Button('Refresh Page', key='__button_download_refresh__'),],
		[sg.Button('Uncheck All', key='__button_download_uncheck_all__',expand_x=True),sg.Button('Check All', key='__button_download_check_all__',expand_x=True),sg.Button('Download Selected', key='__button_download_download__',expand_x=True)],
		[sg.HorizontalSeparator()],
	]

	# format the table holding mod data and checkboxes
	table_layout = [make_column(ugc_col),sg.VerticalSeparator(),
				make_column(name_col, expand_x=True),sg.VerticalSeparator(),
				make_column(author_col),sg.VerticalSeparator(),
				make_column(size_col),sg.VerticalSeparator(),
				sg.Column(checkbox_col_layout)]
	
	# if there are mods to download, add the table layout (in either a scrollable window or as elements)
	if (len(miscompares)+len(not_installed)) != 0:
		if len(ugc_col) > (15+1):	# need to account for the header element in addition to mods
			assembled_layout.append([sg.Column([table_layout], size=(800,420), expand_x=True, expand_y=True, scrollable=True)])
		else:
			assembled_layout.append([sg.Column([table_layout], expand_x=True, expand_y=True)])

	# return the assembled window
	return sg.Window(f'Download Menu', assembled_layout, finalize=True)

# get the default pavlov mod directory location
def get_pavlov_mod_dir_loc():
	pavlov_path = f"{os.getenv('LOCALAPPDATA')}\Pavlov\Saved\Mods"
	try:
		if os.path.exists(pavlov_path):
			return pavlov_path
	except:
		return None

# function to load settings from settings manager
def load_settings(configManager):
	conf_dict = None
	if os.path.exists('PPU.conf'):
		conf_dict = configManager.get_file_conts_as_dict()

	# file doesn't exist so make a new file
	else:
		logging.info('PPU.conf does not exist, creating file')
		configManager.make_new_conf_file()

	# if the dict is none, add keys to conf_dict (will trigger input)
	if conf_dict == None:
		conf_dict = {}

	# check if all keys are in dict, add them if not
	if 'modio_api_token' not in conf_dict:
		conf_dict['modio_api_token'] = ''
	if 'pavlov_mod_dir_path' not in conf_dict:
		conf_dict['pavlov_mod_dir_path'] = ''

	# attempt to use the default pavlov mod dir path
	if conf_dict['pavlov_mod_dir_path'] == '':
		dir_loc = get_pavlov_mod_dir_loc()
		if dir_loc != None:
			conf_dict['pavlov_mod_dir_path'] = dir_loc

	return conf_dict

# save settings file through settings manager
def save_settings(api_token, mod_dir, configManager):
	os.remove('PPU.conf')
	configManager.make_new_conf_file(api_token, mod_dir)

# define layout for the options/settings tab
def make_options_window(sets):
	# left side column for field labels
	def options_label_col():
		return sg.Column([
			[sg.Text('Pavlov Mod Directory Path: ')],
			[sg.Text('Mod.io API Key: ')],
		], element_justification='right')
	# right side column for input fields
	def options_input_col():
		# add saved settings into the input field directly
		return sg.Column([
			[sg.Input(sets['pavlov_mod_dir_path'], key='__input_settings_mod_dir__', expand_x=True)],
			[sg.Input(sets['modio_api_token'], key='__input_settings_api_key__', password_char='*', expand_x=True)],
		], expand_x=True)

	# help text for options window
	help_text = """This program does 3 things:
		1) Check the users subscribed mods against the installed mods, then update out of date mods
		2) Install mods that are subscribed to but not installed
		3) Subscribe to any mod that is installed but not currently subscribed to.

Subscribe to maps and mods at "https://mod.io/g/pavlov", enter your settings and begin downloading.

The following settings are needed to use this program:
		Pavlov Mod Directory Path: the path to the downloaded Pavlov mods folder
		Mod.io API Key: acquired from "https://mod.io/me/access" (read+write) then copied into the modio_api_token variable
Enter these values in the input fields below.

A 'PPU.conf' file and a 'local' folder (that will be filled with images) will be created through the use of this program.
	Please keep the executable with these items or program settings/downloaded mod thumbnails will need to be 
	reentered/redownloaded.
		
If you run into issues using this program, please let me know through the following:
		Github Repo Issue Page: https://github.com/TotalJTM/PyPavlovUpdater/issues
		Email: totaljtm@gmail.com
	 
You can also find me on the Pavlov Push Discord: https://discord.gg/3ngWgM4TwA
"""
	# return full layout
	assembled_layout = [  
		[sg.Text('PyPavlovUpdater Program', justification='center', expand_x=True, font=15)],
		[sg.HorizontalSeparator()],
		[sg.Text(help_text, enable_events=True)],
		[sg.HorizontalSeparator()],
		[sg.Text('PyPavlovUpdater Settings', justification='center', expand_x=True, font=15)],
		[sg.HorizontalSeparator()],
		[options_label_col(), options_input_col()],
		[sg.Button('Update Settings', key='__button_submit_settings__', expand_x=True, pad=(15,15))],
	]

	# return the assembled window
	return sg.Window(f'Options Menu', assembled_layout, resizable=True, finalize=True)

# mod downloader window (something simple with a progress bar)
def make_downloading_window():
	return [
		[sg.Text(f'Downloading UGC:'), sg.Text('', key='__text_ugc__')],
		[sg.Text('', key='__text_name__')],
		[sg.HorizontalSeparator()],
		[sg.Text(f'', key='__text_updates__')],
		[sg.ProgressBar(100, orientation='h', size=(20,20), key='__progress_bar__')]
	]

# get the latest version number of this program from github
def get_latest_program_version():
	resp = requests.get("https://api.github.com/repos/TotalJTM/PyPavlovUpdater/releases/latest")
	if resp.status_code == 200:
		name = resp.json()["tag_name"]
		if 'V' in name:
			maj, min = name.strip('V').split('_')
			return maj, min
		return None, None

# main menu for the pavlov mod updater
def mainmenu(configManager, pvu):
	sg.theme('DefaultNoMoreNagging')

	# attempt to check the latest version of the program from the github release tag
	try:
		lat_maj, lat_min = get_latest_program_version()
		not_latest_vers = True
		if lat_maj != None:
			if int(lat_maj) == major_vers:
				if int(lat_min) == minor_vers:
					not_latest_vers = False
			
			if not_latest_vers:
				sg.Popup("You are running an outdated version of PyPavlovUpdater.\nYou can download a new version from https://github.com/TotalJTM/PyPavlovUpdater/releases", 
				title = 'Out of Date', non_blocking = True, keep_on_top = True)
	except:
		logger.exception(f'Exception when getting latest program version')
		pass

	# make all variables for the window
	options_window = None
	download_window = None
	all_mods_window = None
	subscribed_window = None
	downloading_window = None

	# function for use when downloading mods (window callback to update progress bar)
	# update text/progress bar depending on callbacks within the PavlovUpdater
	def download_window_func(value):
		if value == -3:
			downloading_window['__text_updates__'].update('Getting mod data from Mod.io.')
		if value == -2:
			downloading_window['__text_updates__'].update('Removing old directories.')
		if value == -1:
			downloading_window['__text_updates__'].update('Connecting to Mod.io to download mod.')
		if value == 0:
			downloading_window['__text_updates__'].update('Downloading mod.')
		if value > 0 and value <= 100.00:
			downloading_window['__progress_bar__'].UpdateBar(value)
		if value == 100.0:
			downloading_window['__text_updates__'].update('File Downloaded! Replacing Old Mod.')
		
		downloading_window.refresh()

	# get the installed modlist list
	installed_mods = get_installed_mods(pvu)

	# define the program layout
	layout = [
		[sg.Text(f'You have {len(installed_mods)} Pavlov mods installed', key='__pavlov_installed_text__')],
		[sg.HorizontalSeparator()],
		[sg.Button(f'Open Options Menu', key='__button_open_options_window__', expand_x=True)],
		[sg.Button(f'Open Download Menu', key='__button_open_download_window__', expand_x=True)],
		[sg.Button(f'Open Subscribed Mod Manager', key='__button_open_subscribed_window__', expand_x=True)],
		[sg.Button(f'Open Full Modlist Explorer', key='__button_open_all_mod_window__', expand_x=True)],	
	]

	# create the main window instance for the app
	main_window = sg.Window(f'PyPavlovUpdater V{major_vers}.{minor_vers}', layout, resizable=True, finalize=True) #finalize=True,size=winsize,

	# check that the settings exist, prompt user to fill them out otherwise
	bad_settings = []
	if pvu.pavlov_mod_dir_path == '':
		bad_settings.append('Pavlov Mod Directory Path')
	if pvu.modio_api_token == '':
		bad_settings.append('Mod.io API Key')

	if len(bad_settings) != 0:
		text = 'The following settings need to be updated:\n'
		for set in bad_settings:
			text += f' - {set}\n'
		text += 'Use the Options Menu to set these settings, then you can download mods'
		sg.Popup(text, non_blocking = True, keep_on_top = True, title = 'Settings Error')

	# main gui loop
	while True:
		# get gui events
		try:
			window, event, values = sg.read_all_windows(timeout=100)
		except Exception as e:
			logger.exception(f'Exception when reading windows')
			break

		# timeout event to allow background things to occur
		if event == '__TIMEOUT__':
			continue

		if event == 'Cancel':
			break
		###### handle main window events
		elif window == main_window:
			# handle closing window
			if event == sg.WIN_CLOSED:
				break
			# handle button events to open windows
			elif event == '__button_open_options_window__' and options_window == None:
				settings = load_settings(configManager)
				options_window = make_options_window(settings)
			elif event == '__button_open_download_window__' and download_window == None:
				try:
					download_window = make_download_window(pvu)
				except Exception:
					logging.exception("Error")
			elif event == '__button_open_subscribed_window__' and subscribed_window == None:
				subscribed_window = make_sub_mod_window(pvu)
			elif event == '__button_open_all_mod_window__' and all_mods_window == None:
				all_mods_window = make_all_mod_window(pvu)

		###### handle options window events
		elif window == options_window:
			# handle closing window
			if event == sg.WIN_CLOSED:
				options_window.close()
				options_window = None
			# handle submitting new options
			elif event == '__button_submit_settings__':
				# get new values
				mod_dir = options_window['__input_settings_mod_dir__'].get()
				api_key = options_window['__input_settings_api_key__'].get()
				# update PPU.conf installation
				save_settings(api_key, mod_dir, configManager)
				# update PavlovUpdater object with updated settings
				pvu.pavlov_mod_dir_path = mod_dir
				pvu.modio_api_token = api_key
				# update the installed modlist
				update_installed_mods(pvu)
				good_settings = []
				# check if modlist is empty (could indicate wrong path)
				if len(instmods := get_installed_mods(pvu)) == 0:
					sg.Popup('The mod directory you have selected contains 0 detected Pavlov mods.', keep_on_top = True, title = 'Settings Error')
				else:
					good_settings.append('Pavlov Mod Directory Path')
					main_window['__pavlov_installed_text__'].update(f'You have {len(instmods)} Pavlov mods installed')
				# check if the api key is valid by doing a simple modio request
				resp = pvu.modio_get('me', ret_json=False)
				if resp.status_code != 200:
					sg.Popup('The Mod.io API key you entered is not valid.', keep_on_top = True, title = 'Settings Error')
				else:
					good_settings.append('Mod.io API Key')

				if good_settings:
					text = 'The following settings are valid and saved:\n'
					for set in good_settings:
						text+=f' - {set}\n'
					sg.Popup(text, keep_on_top = True, title = 'Settings Saved')

					# close the menu if settings are valid
					if len(good_settings) == 2:
						options_window.close()
						options_window = None

		###### handle download window events
		elif window == download_window:
			# handle closing window
			if event == sg.WIN_CLOSED:
				download_window.close()
				download_window = None
			# download selected mods from the download window
			elif event == '__button_download_download__':
				# make downloading window
				downloading_window = sg.Window('Downloading...', make_downloading_window(), finalize=True)
				try:
					to_download = []
					# find checked mods, isolate the ugc
					for value in values:
						if '__cbox_download' in value:
							if values[value] == False:
								continue

							nv = value.strip('__').split('_')
							# update the ugc text in the downloading window
							download_ugc = nv[2].strip('UGC')
							downloading_window['__text_ugc__'].update(download_ugc)
							# update the mod name text in the downloading window
							mod_details = retrieve_subscribed_mod_by_ugc(pvu, int(download_ugc))
							downloading_window['__text_name__'].update(mod_details['name'] if mod_details != None else 'Unknown Name')
							# download the mod (provide callback so this function can update the window without recreating download here)
							success = pvu.download_modio_file(int(nv[2].strip('UGC')), int(nv[3]), code_to_run_during_download=download_window_func)
							if success != True:
								sg.popup(f'Could not continue installing mod {nv[2]}, error:\n{success}', non_blocking = True, title = 'Download Error Popup', keep_on_top = True)

				except Exception as e:
					logger.exception(f'Exception in downloading menu')
				finally:
					# update the installed modlist
					update_installed_mods(pvu)
					main_window['__pavlov_installed_text__'].update(f'You have {len(get_installed_mods(pvu))} Pavlov mods installed')
					# close the window since downloading has finished
					downloading_window.close()

				# close download window, updated modlists and restart window
				download_window.close()
				update_installed_mods(pvu)
				update_miscompares(pvu)
				download_window = make_download_window(pvu)

			# check all checkbox fields in download menu
			elif event == '__button_download_check_all__':
				for value in values:
					if '__cbox_download' in value:
						download_window[value].update(True)
			# uncheck all checkbox fields in download menu
			elif event == '__button_download_uncheck_all__':
				for value in values:
					if '__cbox_download' in value:
						download_window[value].update(False)
			# refresh the window and modlists
			elif event == '__button_download_refresh__':
				download_window.close()
				update_installed_mods(pvu)
				update_miscompares(pvu)
				download_window = make_download_window(pvu)

		###### handle subscribed window events
		elif window == subscribed_window:
			# handle closing window
			if event == sg.WIN_CLOSED:
				subscribed_window.close()
				subscribed_window = None
				continue

			# get the filter data so we can let it persist across screen refreshes
			filt = subscribed_window['__subbed_filter__'].get()
			filt_type = subscribed_window['__subbed_filttype__'].get()
			page = int(subscribed_window['__subbed_page_num__'].get())

			# ensure the input fields have a known value/type 
			if filt == '':	# filt should be None if there is no filter input
				filt = None

			if page < 1:	# page cant be less than 1
				page = 1

			### handle buttons that will require the window to be refreshed
			if event == '__button_subbed_page>__':
				page += 1

			if event == '__button_subbed_page<__':
				if page > 1:
					page -= 1

			refresh_page_events = [
				event == '__button_subbed_refresh__',
				event == '__button_subbed_filter__',
				event == '__button_subto_installed__',
				event == '__button_subbed_page>__',
				event == '__button_subbed_page<__',
			]

			# buttons that require refreshing the window
			if any(refresh_page_events):
				# set a variable to hold popup text (if needed later)
				popup_text = None
				# if the subto button was pressed, subscribe to all mods and make popup text
				if event == '__button_subto_installed__':
					miscompares, not_installed, not_subscribed = get_miscompares(pvu)
					success = 0
					not_success = []
					for ugc in not_subscribed:
						resp = pvu.modio_post(f'games/{pvu.pavlov_gameid}/mods/{ugc}/subscribe', ret_json=False)
						if resp:
							if resp.status_code == 201:
								success += 1
								continue
						not_success.append(f' - UGC{ugc}')
					
					if len(not_success) == 0:
						popup_text = f'Successfully subscribed to {success} mods'
					else:
						popup_text = f'Successfully subscribed to {success} mods, could not subscribe to the following mods: \n{", ".join(not_success)}'

				# close window
				subscribed_window.close()
				subscribed_window = None

				# update the subscribed mods if the refresh button was pressed
				if event == '__button_subbed_refresh__':
					update_subscribed_mods(pvu)

				# make the new subscribed mod window with page, filter input and filter combobox inputs
				subscribed_window = make_sub_mod_window(pvu, page, filt, filt_type)

				# do the popup if the object changed
				if popup_text != None:
					sg.popup_ok(popup_text, title='Subscribed Mod Popup', non_blocking=True, keep_on_top =True)

			### handle buttons that dont require the window to be refreshed
			# unsub from a mod and unhide the subscribe button
			elif '__button_unsub_' in event:
				ne = event.strip('__').split('_')	# split event name to get ugc
				resp = pvu.modio_delete(f'games/{pvu.pavlov_gameid}/mods/{ne[2]}/subscribe')
				# check if successfully unsubscribed
				if resp.status_code == 204:
					subscribed_window[event].Update(visible=False)
					subscribed_window[event.replace('unsub', 'sub')].Update(visible=True)
			# sub to a mod and unhide the unsubscribe button
			elif '__button_sub_' in event:
				ne = event.strip('__').split('_')	# split event name to get ugc
				resp = pvu.modio_post(f'games/{pvu.pavlov_gameid}/mods/{ne[2]}/subscribe', ret_json=False)
				# check if successfully subscribed
				if resp.status_code == 201:
					subscribed_window[event].Update(visible=False)
					subscribed_window[event.replace('sub', 'unsub')].Update(visible=True)

			# unsub from a mod and unhide the subscribe button
			elif '__button_like_' in event:
				ne = event.strip('__').split('_')	# split event name to get ugc
				s_ugc = int(ne[2])					# isolate the ugc and make it an int
				mod_rating = get_user_rating_by_ugc(pvu, s_ugc)	# get mod rating
				if mod_rating <= 0:	# if mod is not liked, send request to like it
					resp = pvu.modio_rate_mod(s_ugc, like=True)
				else:	# if mod is liked, send request to un-like it
					resp = pvu.modio_rate_mod(s_ugc)

				# check if mod rating was updated, set button colors/text depending on state
				if resp == True:
					if mod_rating <= 0:
						subscribed_window[event].Update(text='Liked', button_color=actv_green)
						subscribed_window[event.replace('like','dislike')].Update(button_color=default_btn)
					else:
						subscribed_window[event].Update(text='Like', button_color=default_btn)
				# update the user ratings before continuing
				update_user_ratings(pvu)
					
			# sub to a mod and unhide the unsubscribe button
			elif '__button_dislike_' in event:
				ne = event.strip('__').split('_')	# split event name to get ugc
				s_ugc = int(ne[2])					# isolate the ugc and make it an int
				mod_rating = get_user_rating_by_ugc(pvu, s_ugc)	# get mod rating
				if mod_rating >= 0:	# if mod is not disliked, send request to dislike it
					resp = pvu.modio_rate_mod(s_ugc, dislike=True)
				else: 	# if mod is disliked, send request to un-dislike it
					resp = pvu.modio_rate_mod(s_ugc)

				# check if mod rating was updated, set button colors/text depending on state
				if resp == True:
					if mod_rating >= 0:
						subscribed_window[event].Update(text='Disliked', button_color=actv_red)
						subscribed_window[event.replace('dislike','like')].Update(button_color=default_btn)
					else:
						subscribed_window[event].Update(text='Dislike', button_color=default_btn)
				# update the user ratings before continuing
				update_user_ratings(pvu)

		###### handle all mod window events
		elif window == all_mods_window:
			# handle closing window
			if event == sg.WIN_CLOSED:
				all_mods_window.close()
				all_mods_window = None
				continue

			# get the filter data so we can let it persist across screen refreshes
			filt = all_mods_window['__all_mod_filter__'].get()
			filt_type = all_mods_window['__all_mod_filttype__'].get()
			page = int(all_mods_window['__all_mod_page_num__'].get())

			# ensure the input fields have a known value/type 
			if filt == '':	# filt should be None if there is no filter input
				filt = None

			if page < 1:	# page cant be less than 1
				page = 1

			### handle buttons that will require the window to be refreshed
			if event == '__button_all_mod_page>__':
				page += 1

			if event == '__button_all_mod_page<__':
				if page > 1:
					page -= 1

			refresh_page_events = [
				event == '__button_all_mod_refresh__',
				event == '__button_all_mod_filter__',
				event == '__button_all_mod_page>__',
				event == '__button_all_mod_page<__',
			]

			# buttons that require refreshing the window
			if any(refresh_page_events):
				# set a variable to hold popup text (if needed later)
				popup_text = None
				
				# close window
				all_mods_window.close()
				all_mods_window = None

				# update the subscribed mods if the refresh button was pressed
				if event == '__button_all_mod_refresh__':
					update_full_mods(pvu)
					update_subscribed_mods(pvu)

				# make the new subscribed mod window with page, filter input and filter combobox inputs
				all_mods_window = make_all_mod_window(pvu, page, filt, filt_type)

				# do the popup if the object changed
				if popup_text != None:
					sg.popup_ok(popup_text, title='All Mod Popup', non_blocking=True, keep_on_top =True)

			### handle buttons that dont require the window to be refreshed
			# unsub from a mod and unhide the subscribe button
			elif '__button_unsub_' in event:
				ne = event.strip('__').split('_')	# split event name to get ugc
				resp = pvu.modio_delete(f'games/{pvu.pavlov_gameid}/mods/{ne[2]}/subscribe')
				# check if successfully unsubscribed
				if resp.status_code == 204:
					all_mods_window[event].Update(visible=False)
					all_mods_window[event.replace('unsub', 'sub')].Update(visible=True)
			# sub to a mod and unhide the unsubscribe button
			elif '__button_sub_' in event:
				ne = event.strip('__').split('_')	# split event name to get ugc
				resp = pvu.modio_post(f'games/{pvu.pavlov_gameid}/mods/{ne[2]}/subscribe', ret_json=False)
				# check if successfully subscribed
				if resp.status_code == 201:
					all_mods_window[event].Update(visible=False)
					all_mods_window[event.replace('sub', 'unsub')].Update(visible=True)

			# unsub from a mod and unhide the subscribe button
			elif '__button_like_' in event:
				ne = event.strip('__').split('_')	# split event name to get ugc
				s_ugc = int(ne[2])					# isolate the ugc and make it an int
				mod_rating = get_user_rating_by_ugc(pvu, s_ugc)	# get mod rating
				if mod_rating <= 0:	# if mod is not liked, send request to like it
					resp = pvu.modio_rate_mod(s_ugc, like=True)
				else:	# if mod is liked, send request to un-like it
					resp = pvu.modio_rate_mod(s_ugc)

				# check if mod rating was updated, set button colors/text depending on state
				if resp == True:
					if mod_rating <= 0:
						all_mods_window[event].Update(text='Liked', button_color=actv_green)
						all_mods_window[event.replace('like','dislike')].Update(button_color=default_btn)
					else:
						all_mods_window[event].Update(text='Like', button_color=default_btn)
				# update the user ratings before continuing
				update_user_ratings(pvu)
					
			# sub to a mod and unhide the unsubscribe button
			elif '__button_dislike_' in event:
				ne = event.strip('__').split('_')	# split event name to get ugc
				s_ugc = int(ne[2])					# isolate the ugc and make it an int
				mod_rating = get_user_rating_by_ugc(pvu, s_ugc)	# get mod rating
				if mod_rating >= 0:	# if mod is not disliked, send request to dislike it
					resp = pvu.modio_rate_mod(s_ugc, dislike=True)
				else: 	# if mod is disliked, send request to un-dislike it
					resp = pvu.modio_rate_mod(s_ugc)

				# check if mod rating was updated, set button colors/text depending on state
				if resp == True:
					if mod_rating >= 0:
						all_mods_window[event].Update(text='Disliked', button_color=actv_red)
						all_mods_window[event.replace('dislike','like')].Update(button_color=default_btn)
					else:
						all_mods_window[event].Update(text='Dislike', button_color=default_btn)
				# update the user ratings before continuing
				update_user_ratings(pvu)


		###### handle other windows (do nothing)			
		else:
			pass

	# close the main window
	main_window.close()

if __name__ == "__main__":
	logging.basicConfig(filename="pypavlovupdater.log",
						format='%(asctime)s %(message)s',
						filemode='w+')
	logger = logging.getLogger()
	# logger.addHandler(logging.StreamHandler(sys.stdout))

	logger.setLevel(logging.INFO)
	logger.info(f'Version {major_vers}.{minor_vers}')

	# make settings manager object for use later
	configurationManager = settings_manager.Conf_Manager('PPU.conf', logger)

	# load saved settings
	settings = load_settings(configurationManager)

	# create pavlov updater object from saved settings
	pavlov_updater = pavlovupdater.PavlovUpdater(settings['pavlov_mod_dir_path'], settings['modio_api_token'], logger)

	try:
		# launch gui main menu
		while True:
			ret = mainmenu(configurationManager, pavlov_updater)
			if ret == 'continue':
				continue
			else:
				break
	except Exception as e:
		logger.exception(f'Exception in main loop')
		sg.Popup(f'Program encountered an error.\nPlease report this error by making an issue on the Github repo and attaching the log file in executable directory.', title='Program Error')