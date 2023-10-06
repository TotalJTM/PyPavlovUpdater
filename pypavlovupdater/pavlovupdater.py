import requests
import json
import os
import tempfile
import zipfile
import hashlib

class PavlovUpdater:
	# need to initialize the class with:
	#	pavlov_mod_dir_path = path to the pavlov mod directory
	#	modio_api_token = Mod.io API token this program will use to read+write data from/to the Mod.io API
	# API tokens can be acquired from Mod.IO on the "https://mod.io/me/access" page
	def __init__(self, pavlov_mod_dir_path, modio_api_token) -> None:
		self.pavlov_mod_dir_path = pavlov_mod_dir_path
		self.pavlov_gameid = '3959'
		# self.settings_path = ''
		self.modio_api_url = 'https://api.mod.io/v1'
		self.modio_api_token = modio_api_token
		self.target_os = 'windows'

	# make a get request to modio
	#	route = address to make request at (ex. games/3959/mods)
	#	ret_json = converts response to json if True, return raw response if False
	#	raw = the function will not add the modio api url, what is supplied to route is the address the request will be made to
	def modio_get(self, route, ret_json=True, raw=False):
		# assemble address and header
		addr = f"{self.modio_api_url}/{route}"
		head = {'Authorization': f'Bearer {self.modio_api_token}', 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
		# send request
		response = requests.get(addr if raw==False else route, params={}, headers=head)
		# convert the response to a json dict
		if ret_json == True:
			d = response.json()
			if 'error' in d.keys():
				print(f"Error code {d['error']['code']}, {d['error']['message']}")
				return None

		if ret_json:
			return d
		else:
			return response
		
	# make a post request to modio
	#	route = address to make request at (ex. games/3959/mods)
	def modio_post(self, route):
		# assemble address and header
		addr = f"{self.modio_api_url}/{route}"
		head = {'Authorization': f'Bearer {self.modio_api_token}', 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
		# send request
		response = requests.post(addr, params={}, headers=head)
		# convert the response to a json dict
		d = response.json()
		if 'error' in d.keys():
			print(f"Error code {d['error']['code']}, {d['error']['message']}")
			return None

		return d
	
	# get the full modlist for Pavlov
	def get_pavlov_modlist(self):
		resp = self.modio_get(f'games/{self.pavlov_gameid}/mods')
		if resp == None:
				return None
		return resp
	
	# get the full subscription list of the user 
	# returns a dictionary entry for each subscribed mod with attributes listed below
	def get_subscribed_modlist(self):
		mods = []
		# get initial subscribed mods for pavlov (first 100 entrys)
		init_resp = self.modio_get(f'me/subscribed?game_id={self.pavlov_gameid}')
		if init_resp == None:
				return None
		# print(init_resp)

		# create a dict to enter into the mods folder
		def make_entry(m):
			modfile_live_win = None
			for p in m['platforms']:
				# only use downloads for the target operating system
				if p['platform'] == self.target_os:
					modfile_live_win = p['modfile_live']
			
			if modfile_live_win == None:
				return None

			# attributes in a subscribed modlist entry
			return {
				'id':m['id'], 
				'name':m['name'],
				'name_id':m['name_id'], 
				'maker':m['submitted_by']['username'], 
				'date_added':m['date_added'], 
				'date_updated':m['date_updated'], 
				'date_live':m['date_live'], 
				'modfile':{
					'id': modfile_live_win,
					'date_added':m['modfile']['date_added'],
					'filesize':m['modfile']['filesize'],
					'filehash':m['modfile']['filehash'],
					'version':m['modfile']['version'],
					'binary_url':m['modfile']['download']['binary_url'],
				}
			}

		# go through response and make/add entrys to the mods arr
		for m in init_resp['data']:
			entry = make_entry(m)
			if entry != None:
				mods.append(entry)

		# calculate number of pages to get all users subscribed mods
		total_pages = int(init_resp['result_total']/init_resp['result_count'])+1

		# iter through pages calculated
		for i in range(1,total_pages):
			# get new response (but paginated)
			resp = self.modio_get(f'me/subscribed?game_id={self.pavlov_gameid}&_offset={int(i*100)}')#?game-id={self.pavlov_gameid}
			if resp == None:
				return None
			# go through response and make/add entrys to the mods arr
			for m in resp['data']:
				entry = make_entry(m)
				if entry != None:
					mods.append(entry)
				
		return mods
	
	# get a list of installed mods (from Pavlov mod directory)
	# returns a dictionary of UGC codes and versions (taint file contents) (ex. {'UGC3262677': 4333298,...})
	def get_installed_modlist(self):
		mods = {}
		# iter through pavlov mod directory
		for path, folders, files in os.walk(self.pavlov_mod_dir_path):
			# iter through folders to get UGC of each mod in the folder
			for folder in folders:
				if 'UGC' in folder:
					ugc = int(folder.strip('UGC'))

					# also try to read the 'taint' file (where the version is stored)
					version = None
					try:
						with open(os.path.join(path, folder, 'taint'), 'r') as t:
							version = int(t.read())

						if version != None:
							mods[ugc] = version

					except:
						continue

		return mods
	
	# download a mod file from mod.io
	#	ugc = UGC code of the map to download
	#	version = version id of the map version that will be installed
	#	code_to_run_during_download = optional function call to replace code executed during mod download (for a progress bar)
	def download_modio_file(self, ugc, version, code_to_run_during_download=None):
		# get mod file information
		resp = self.modio_get(f'games/3959/mods/{ugc}/files/{version}')
		if resp == None:
			return None

		# check the virus status of the file
		if resp['virus_positive'] != 0:
			print(f'Virus detected, skipping')
			return None

		# check if the mod directory exists
		if os.path.exists(f'{self.pavlov_mod_dir_path}/UGC{ugc}'):
			# iter through the UGC folder to delete files/folders
			try:
				for path, folders, files in os.walk(f'{self.pavlov_mod_dir_path}/UGC{ugc}/Data'):
					for f in files:
						# print(f'{path}/{f}')
						os.remove(f'{path}/{f}')
				for path, folders, files in os.walk(f'{self.pavlov_mod_dir_path}/UGC{ugc}'):
					for f in files:
						# print(f'{path}/{f}')
						os.remove(f'{path}/{f}')
					for f in folders:
						# print(f'{path}/{f}')
						os.rmdir(f'{path}/{f}')
			except Exception as e:
				print(f'Skipped removing dir items : {e}')
		# if the directory doesnt exist, make the directory
		else:
			os.mkdir(f'{self.pavlov_mod_dir_path}/UGC{ugc}')
		# make the Data directory
		os.mkdir(f'{self.pavlov_mod_dir_path}/UGC{ugc}/Data')

		# this code segment is from this site: https://www.alpharithms.com/progress-bars-for-python-downloads-580122/
		# use a context manager to make an HTTP request and file
		import sys, time
		head = {'Authorization': f'Bearer {self.modio_api_token}', 'Accept': 'application/json'}
		print(f'Making request to Mod.io')
		# make the request
		with requests.get(resp['download']['binary_url'], headers=head) as r:
			print('Downloading mod')
			with tempfile.NamedTemporaryFile(delete=False) as file:
				if code_to_run_during_download == None:
					code_to_run_during_download()
				else:
					# Get the total size, in bytes, from the response header
					total_size = int(r.headers.get('Content-Length'))
					# Define the size of the chunk to iterate over (Mb)
					chunk_size = 1000
					# iterate over every chunk and calculate % of total
					for i, chunk in enumerate(r.iter_content(chunk_size=chunk_size)):
						# calculate current percentage
						c = i * chunk_size / total_size * 100
						# write current % to console, pause for .1ms, then flush console
						sys.stdout.write(f"\r{round(c, 4)}%")
						sys.stdout.flush()

				# write 100% to the terminal
				sys.stdout.write(f"\r100.0000%")
				sys.stdout.flush()
				
				# update temp name var and write to the file
				print('\nWriting to file')
				temp_name = file.name
				file.write(r.content)

		# unzip the downloaded file and place it in the Data directory
		with zipfile.ZipFile(temp_name, 'r') as z:
			z.extractall(f"{self.pavlov_mod_dir_path}/UGC{ugc}/Data/")

		# remove temp file
		os.remove(temp_name)

		# open the 'taint' file and write the new version
		with open(f'{self.pavlov_mod_dir_path}/UGC{ugc}/taint', 'w') as f:
			f.write(f'{version}')

	# find miscomparisons between modio latest mod versions and installed mod versions
	#	subscribed_list = list of subscribed mod files (expects output from get_subscribed_modlist())
	#	installed_list = list of installed mod files (expects output from get_installed_modlist())
	def find_miscompares_in_modlists(self, subscribed_list, installed_list):
		miscompares = []
		not_installed = []
		not_subscribed = []
		subscribed_ids = []
		# print table header and iter mods in subscribed_list
		print(f'Status     |  {"Map Name":50s}  | UGC        | Version (modio : installed)')
		for item in subscribed_list:
			# add id to subscribed ids (used for not_subscribe arr assembly)
			subscribed_ids.append(item['id'])
			# check if the ugc from the sub_modlist is in installed_list
			if item['id'] in installed_list:
				# compare the version from mod.io against the taint file version
				if item['modfile']['id'] == installed_list[item['id']]:
					print(f'Up to date | "{item["name"]:50s}" | UGC{item["id"]} | {item["modfile"]["id"]} == {installed_list[item["id"]]}')
				else:
					print(f'Mismatch in id | "{item["name"]:46s}" | UGC{item["id"]} | {item["modfile"]["id"]} != {installed_list[item["id"]]}')
					# add to miscompare arr since it is different from the latest version
					miscompares.append(item)
			else:
				print(f'Mod not installed | {" ":43s} | UGC{item["id"]}')
				# add to not_installed arr since id is not installed
				not_installed.append(item)
		
		# check if all installed keys are part of user subscriptions
		for inst_key in installed_list.keys():
			if inst_key not in subscribed_ids:
				not_subscribed.append(inst_key)

		return miscompares, not_installed, not_subscribed
	
	# update the mods installed in pavlov mod directory
	def update_subscribed_mods(self):
		# get list of subscribed mods
		subs_list = self.get_subscribed_modlist()
		print(f"=== There are {len(subs_list)} subscribed mods ===")

		# get list of installed mods
		installed_mods = self.get_installed_modlist()

		# find mods that are 1) not latest version, 2) not installed, 3) installed but not subscribed
		miscompares, not_installed, not_subscribed = self.find_miscompares_in_modlists(subs_list, installed_mods)
		
		print(f'Miscompared: {len(miscompares)}, Not Installed: {len(not_installed)}, Not Subscribed: {len(not_subscribed)}')
		
		# if there are miscompares, download the latest version
		if len(miscompares) > 0:
			print(f'=== Updating out of date mods ===')
			for mod in miscompares:
				print(f'-- Updating {mod["name"]} --')
				self.download_modio_file(mod['id'], mod['modfile']['id']) 
			pass

		# if there are mods not installed, download the latest version
		if len(not_installed) > 0:
			print(f'=== Installing not-yet installed mods ===')
			for mod in not_installed:
				print(f'-- Installing {mod["name"]} --')
				self.download_modio_file(mod['id'], mod['modfile']['id']) 
			pass 

		# if there are mods downloaded but are not subscribed to, post subscription request
		if len(not_subscribed) > 0:
			print(f'=== Subscribing to not-yet subscribed mods ===')
			for modid in not_subscribed:
				print(f'-- Subscribing to UGC{modid} --')
				resp = self.modio_post(f'games/{self.pavlov_gameid}/mods/{modid}/subscribe')
			pass 


if __name__ == "__main__":
	# use the configuration manager to load configuration variables from the .conf file
	import settings_manager

	conf_dict = None
	cm = settings_manager.Conf_Manager('PPU.conf')
	if os.path.exists('PPU.conf'):
		conf_dict = cm.get_file_conts_as_dict()

	# file doesnt exist so make a new file
	else:
		print('PPU.conf does not exist, creating file')
		cm.make_new_conf_file()

	# create variables to hold state of api, directory vars and whether the conf should be updated
	api_ok = False
	dir_ok = False
	update = False

	# if the dict is none, add keys to conf_dict (will trigger input)
	if conf_dict == None:
		conf_dict = {'modio_api_token':'', 'pavlov_mod_dir_path':''}

	# check if 'modio_api_token' str in dict is empty, get the user to input a valid API token (until ctrl+c)
	if conf_dict['modio_api_token'] == "":
		try:
			modio_api_token_input = None
			while modio_api_token_input == None:
				modio_api_token_input = input('Paste the Mod.io API token: ')
				if modio_api_token_input != "" and len(modio_api_token_input) > 64:
					api_ok = True
					update = True
					conf_dict['modio_api_token'] = modio_api_token_input
				else:
					print(f'Invalid API token input')
					modio_api_token_input = None
		except:
			print(f'Canceled attempt to enter API token')
	else:
		api_ok = True
	
	# check if 'pavlov_mod_dir_path' str in dict is empty, get the user to input a valid API token (until ctrl+c)
	if conf_dict['pavlov_mod_dir_path'] == "":
		try:
			pavlov_mod_dir_path_input = None
			while pavlov_mod_dir_path_input == None:
				pavlov_mod_dir_path_input = input('Paste the path to the Pavlov mod directory: ')
				if pavlov_mod_dir_path_input != "":
					dir_ok = True
					update = True
					conf_dict['pavlov_mod_dir_path'] = pavlov_mod_dir_path_input
				else:
					print(f'Invalid Pavlov directory input')
					pavlov_mod_dir_path_input = None
		except:
			print(f'Canceled attempt to enter API token')
	else:
		dir_ok = True

	# update the configuration if either the API or mod dir have changed
	if update:
		os.remove('PPU.conf')
		cm.make_new_conf_file(conf_dict['modio_api_token'], conf_dict['pavlov_mod_dir_path'])
	
	# check if there is an API string and mod directory path
	if api_ok and dir_ok:
		# create pavlov updater object
		pu = PavlovUpdater(pavlov_mod_dir_path=conf_dict['pavlov_mod_dir_path'], modio_api_token=conf_dict['modio_api_token'])
		# get all subscribed modes
		print(f'Updating subscribed mods')
		pu.update_subscribed_mods()
	
		print('=== Finished Updating ===')