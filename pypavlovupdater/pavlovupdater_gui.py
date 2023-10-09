import pavlovupdater
import settings_manager
import PySimpleGUI as sg
from datetime import datetime
import os
import io
from PIL import Image


major_vers = 1
minor_vers = 0

### a few sets of functions to minimize the amount of API calls ###
# globally defined subscribed mod array 
subscribbed_mods = None
# function to update modlist
def update_subscribed_mods(pvu):
	global subscribbed_mods
	subscribbed_mods = pvu.get_subscribed_modlist()
# function to get modlist without defining global
def get_subscribed_mods(pvu):
	global subscribbed_mods
	if subscribbed_mods == None:
		update_subscribed_mods(pvu)
	return subscribbed_mods

# globally defined insatlled mod array 
installed_mods = None
# function to update modlist
def update_installed_mods(pvu):
	global installed_mods
	installed_mods = pvu.get_installed_modlist()
# function to get modlist without defining global
def get_installed_mods(pvu):
	global installed_mods
	if installed_mods == None:
		update_installed_mods(pvu)
	return installed_mods

# globally defined miscompare array vars
miscompares = None
not_installed = None
not_subscribed = None
# function to update modlists
def update_miscompares(pvu):
	global miscompares, not_installed, not_subscribed
	miscompares, not_installed, not_subscribed = pvu.find_miscompares_in_modlists(get_subscribed_mods(pvu), get_installed_mods(pvu), printout=False)
# function to get modlists without defining global
def get_miscompares(pvu):
	global miscompares, not_installed, not_subscribed
	if miscompares == None:
		update_miscompares(pvu)
	return miscompares, not_installed, not_subscribed


### GUI functions ###
# global dict to hold created images (so they dont have to get loaded again)
image_bios = {}
# define the layout for mod lists
def make_mod_item_frame(pvu, mod):
	global image_bios
	# make locals folder to store mod thumbnails
	if not os.path.exists('local'):
		os.mkdir('local')
	# check if the image has already been loaded
	if str(mod['id']) not in image_bios:
		# make an address, check if it exists
		logo_faddr = f'local/UGC{mod["id"]}_logo.png'
		if not os.path.exists(logo_faddr):
			try:
				# download an image and write it to faddr
				image_bin = pvu.get_modio_image(mod['logo'])
				with open(logo_faddr, 'wb') as f:
					f.write(image_bin)
			except Exception as e:
				# default to a pysimplegui emoji
				print(e)
				logo_faddr = sg.EMOJI_BASE64_HAPPY_THUMBS_UP

		# resize the image and load it into the global dict
		image = Image.open(logo_faddr)
		image.thumbnail((200, 200))
		bio = io.BytesIO()
		image.save(bio, format="PNG")

		image_bios[str(mod['id'])] = bio

	# make timestamp for last updated text
	date_str = datetime.fromtimestamp(mod['date_updated'])

	# image on the left
	col_left = [
		[sg.Image(data=image_bios[str(mod['id'])].getvalue())]
	]
	# mod information next to the image
	col_mid = [
		[sg.Text(f"{mod['name']}")],
		[sg.Text(f"By {mod['maker']}")],
		[sg.Text(f"Version: {mod['modfile']['version']}")],
		[sg.Text(f"Last Updated {date_str}")],
	]
	# mod options on the right
	col_right = [
		[sg.Button('Unsubscribe', key=f'__button_unsub_{mod["id"]}__', expand_x=True)],
		[sg.Button('Subscribe', key=f'__button_sub_{mod["id"]}__', visible=False, expand_x=True)],
	]

	# lay out columns of above elements to go in frame
	conts = [
		[sg.Column(col_left), sg.Column(col_mid,element_justification='left', expand_x=True), sg.Column(col_right, element_justification='right')],
		# [sg.Text(mod['description'])],
	]

	# return the assembled frame
	return sg.Frame(f"UGC{mod['id']}", conts, expand_x=True)



# define layout for the subscribed tab
def make_sub_mod_window(pvu, mod_filter=None):
	# get list of subscribed mods
	mods = get_subscribed_mods(pvu)
	if mods == None:
		return [[sg.Text('Could not get subscribed mod list')]]

	# get list of installed mods
	installed_mods = get_installed_mods(pvu)

	# find mods that are 1) not latest version, 2) not installed, 3) installed but not subscribed
	miscompares, not_installed, not_subscribed = get_miscompares(pvu)

	# make all of the mods into mod_item_layout items
	mods_left = []
	mods_right = []
	count = 1
	for mod in mods:
		# apply filter if filter var not None
		if mod_filter != None and mod_filter.lower() not in mod['name'].lower():
			continue
			
		if count%2 == True:
			mods_left.append([make_mod_item_frame(pvu, mod)])
		else:
			mods_right.append([make_mod_item_frame(pvu, mod)])
		count += 1

	# assemble the layout into an array
	mods_layout_arr = [[sg.Column(mods_left, key='__subbed_mods_left__', vertical_alignment='top'), sg.Column(mods_right, key='__subbed_mods_right__', vertical_alignment='top')]]

	# make the larger subscribed mod window layout with the newly assembled mod layout
	assembled_layout = [
		[sg.Text(f'{len(mods)-len(miscompares)-len(not_installed)}/{len(mods)} Up to Date, {len(miscompares)} Out of Date, {len(not_installed)} Not Installed, {len(not_subscribed)} Not Subscribed'), 
			sg.Column([[]], expand_x=True), 
			sg.Button('Subscribe to nonsubscribed-but-installed mods', key='__button_subto_installed__'),
			sg.Button('Refresh Modlist', key='__button_subbed_refresh__'),],
		[sg.HorizontalSeparator()],
		[sg.Text('Filter (name)'), sg.Input('', key='__subbed_filter__', expand_x=True), sg.Button('Submit', key='__button_subbed_filter__')],
		[sg.Column(mods_layout_arr, key='__sub_mod_scrollable__', scrollable=True, justification='right', expand_x=True, expand_y=True)]#vertical_scroll_only=True,
	]

	# return the assembled window
	return sg.Window(f'Subscribed Mods', assembled_layout, size=(1350,500), resizable=True, finalize=True)

# define layout for downloads menu
def make_download_window(pvu):
	subbed_mods = get_subscribed_mods(pvu)
	if subbed_mods == None:
		return [[sg.Text('Could not get subscribed mod list')]]

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
	checkbox_col_layout = [[sg.Text('Download?')]]
	for i, ugc in enumerate(ugc_col):
		# hack so I can use the array for table headers
		if i==0:
			continue
		k = f'__cbox_download_UGC{ugc}_{modfile_id[i]}__'
		checkbox_col_layout.append([sg.CBox('', key=k)])
	
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
		if len(ugc_col) >= 10:
			assembled_layout.append([sg.Column([table_layout], expand_x=True, expand_y=True, scrollable=True, vertical_scroll_only=True)])
		else:
			assembled_layout.append(table_layout)

	# return the assembled window
	return sg.Window(f'Download Menu', assembled_layout, finalize=True)


# make settings manager object for use later
cm = settings_manager.Conf_Manager('PPU.conf')

# function to load settings from settings manager
def load_settings():
	conf_dict = None
	if os.path.exists('PPU.conf'):
		conf_dict = cm.get_file_conts_as_dict()

	# file doesnt exist so make a new file
	else:
		print('PPU.conf does not exist, creating file')
		cm.make_new_conf_file()

	# if the dict is none, add keys to conf_dict (will trigger input)
	if conf_dict == None:
		conf_dict = {}

	# check if all keys are in dict, add them if not
	if 'modio_api_token' not in conf_dict:
		conf_dict['modio_api_token'] = ''
	if 'pavlov_mod_dir_path' not in conf_dict:
		conf_dict['pavlov_mod_dir_path'] = ''

	return conf_dict

# save settings file through settings manager
def save_settings(api_token, mod_dir):
	os.remove('PPU.conf')
	cm.make_new_conf_file(api_token, mod_dir)

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
\t1) Check the users subscribed mods against the installed mods, then update out of date mods
\t2) Install mods that are subscribed to but not installed
\t3) Subscribe to any mod that is installed but not currently subscribed to.

This GUI tool can be used to perform all of the above functionality."""
	# return full layout
	assembled_layout = [  
		[sg.Text('PyPavlovUpdater Program', justification='center', expand_x=True, font=15)],
		[sg.HorizontalSeparator()],
		[sg.Text(help_text)],
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
		[sg.Text(f'Mod UGC:'), sg.Text('', key='__text_ugc__')],
		[sg.Text(f'', key='__text_updates__')],
		[sg.ProgressBar(100, orientation='h', size=(20,20), key='__progress_bar__')]
	]

# main menu for the pavlov mod updater
def mainmenu(settings, pvu):
	sg.theme('DefaultNoMoreNagging')

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
	installed_mods = pvu.get_installed_modlist()

	# define the program layout
	layout = [
		[sg.Text(f'You have {len(installed_mods)} Pavlov mods installed')],
		[sg.HorizontalSeparator()],
		[sg.Button(f'Open Options Menu', key='__button_open_options_window__', expand_x=True)],
		[sg.Button(f'Open Download Menu', key='__button_open_download_window__', expand_x=True)],
		[sg.Button(f'Open Subscribed Mod Manager', key='__button_open_subscribed_window__', expand_x=True)],	
	]

	# create the main window instance for the app
	main_window = sg.Window(f'PyPavlovUpdater V{major_vers}.{minor_vers}', layout, resizable=True, finalize=True) #finalize=True,size=winsize,

	# main gui loop
	while True:
		# get gui events
		try:
			window, event, values = sg.read_all_windows(timeout=100)
		except Exception as e:
			print(f'Closed with error: {e}')
			break

		# timeout event to allow background things to occur
		if event == '__TIMEOUT__':
			continue

		# print(event)

		if event == 'Cancel':
			break
		# handle main window events
		elif window == main_window:
			# handle closing window
			if event == sg.WIN_CLOSED:
				break
			# handle button events to open windows
			elif event == '__button_open_options_window__' and options_window == None:
				options_window = make_options_window(settings)
			elif event == '__button_open_download_window__' and download_window == None:
				download_window = make_download_window(pvu)
			elif event == '__button_open_subscribed_window__' and subscribed_window == None:
				subscribed_window = make_sub_mod_window(pvu)

		# handle options window events
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
				save_settings(api_key, mod_dir)
				# update PavlovUpdater object with updated settings
				pvu.pavlov_mod_dir_path = mod_dir
				pvu.modio_api_token = api_key

		# handle download window events
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
							nv = value.strip('__').split('_')
							# update the ugc text field in the downloading window
							downloading_window['__text_ugc__'].update(nv[2].strip('UGC'))
							# download the mod (provide callback so this function can update the window without recreating download here)
							pvu.download_modio_file(int(nv[2].strip('UGC')), int(nv[3]), code_to_run_during_download=download_window_func)
				except Exception as e:
					print(f'error occured {e}')
				finally:
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

		# handle subscribed window events
		elif window == subscribed_window:
			# handle closing window
			if event == sg.WIN_CLOSED:
				subscribed_window.close()
				subscribed_window = None
			# buttons that require refreshing the window
			elif event == '__button_subbed_refresh__' or event == '__button_subbed_filter__' or event == '__button_subto_installed__':
				# get the filter data if this is the 'subbed filter' button
				if event == '__button_subbed_filter__':
					filt = subscribed_window['__subbed_filter__'].get()
				# set a variable to hold popup text (if needed later)
				popup_text = None
				# if the subto button was pressed, subscribe to all mods and make popup text
				if event == '__button_subto_installed__':
					miscompares, not_installed, not_subscribed = get_miscompares(pvu)
					success = 0
					not_success = []
					for ugc in not_subscribed:
						resp = pvu.modio_post(f'games/{pvu.pavlov_gameid}/mods/{ugc}/subscribe')
						if resp:
							if resp.status_code == 201:
								success += 1
								continue
						not_success.append(f'UGC{ugc}')
					
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

				# if the filter was applied, add it to mod window construction
				if event == '__button_subbed_filter__':
					subscribed_window = make_sub_mod_window(pvu, filt)
				# otherwise remake window like normal
				else:
					subscribed_window = make_sub_mod_window(pvu)

				# do the popup if the object changed
				if popup_text != None:
					sg.popup_ok(popup_text, title='Subscribed Mod Popup')

			# unsub from a mod and unhide the subscribe button
			elif '__button_unsub_' in event:
				ne = event.strip('__').split('_')
				resp = pvu.modio_delete(f'games/{pvu.pavlov_gameid}/mods/{ne[2]}/subscribe')
				if resp.status_code == 204:
					subscribed_window[event].Update(visible=False)
					subscribed_window[event.replace('unsub', 'sub')].Update(visible=True)
			# sub to a mod and unhide the unsubscribe button
			elif '__button_sub_' in event:
				ne = event.strip('__').split('_')
				resp = pvu.modio_post(f'games/{pvu.pavlov_gameid}/mods/{ne[2]}/subscribe', ret_json=False)
				if resp.status_code == 201:
					subscribed_window[event].Update(visible=False)
					subscribed_window[event.replace('sub', 'unsub')].Update(visible=True)
		else:
			pass
	# close the main window
	main_window.close()

if __name__ == "__main__":
	print(f'PyPavlovUpdater GUI Version {major_vers}.{minor_vers}')

	# load saved settings
	settings = load_settings()

	# create pavlov updater object from saved settings
	pavlov_updater = pavlovupdater.PavlovUpdater(settings['pavlov_mod_dir_path'], settings['modio_api_token'])
	
	# launch gui main menu
	while True:
		ret = mainmenu(settings, pavlov_updater)
		if ret == 'continue':
			continue
		else:
			break