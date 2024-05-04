import json
import os
import tempfile
import zipfile
import hashlib

import requests


major_vers = 1
minor_vers = 4

class PavlovUpdater:
	# need to initialize the class with:
	#	pavlov_mod_dir_path = path to the pavlov mod directory
	#	modio_api_token = Mod.io API token this program will use to read+write data from/to the Mod.io API
	# API tokens can be acquired from Mod.IO on the "https://mod.io/me/access" page
	def __init__(self, pavlov_mod_dir_path, modio_api_token, logging_obj) -> None:
		self.pavlov_mod_dir_path = pavlov_mod_dir_path
		self.pavlov_gameid = '3959'
		# self.settings_path = ''
		self.modio_api_url = 'https://api.mod.io/v1'
		self.modio_api_token = modio_api_token
		self.target_os = 'windows'
		self.logger = logging_obj

	# make a get request to modio
	#	route = address to make request at (ex. games/3959/mods)
	#	ret_json = converts response to json if True, return raw response if False
	#	raw = the function will not add the modio api url, what is supplied to route is the address the request will be made to
	def modio_get(self, route, ret_json=True, raw=False):
		self.logger.info(f'Get request {route}')
		# assemble address and header
		addr = f"{self.modio_api_url}/{route}"
		head = {'Authorization': f'Bearer {self.modio_api_token}', 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json', 'X-Modio-Platform': self.target_os}
		# send request
		response = requests.get(addr if raw==False else route, params={}, headers=head)
		# convert the response to a json dict
		if ret_json == True:
			d = response.json()
			if 'error' in d.keys():
				self.logger.error(f"response containted error {d['error']['code']}, {d['error']['message']}")
				return f"error{d['error']['code']}"

		if ret_json:
			return d
		else:
			return response
		
	# make a post request to modio
	#	route = address to make request at (ex. games/3959/mods)
	def modio_post(self, route, ret_json=True, params={}):
		self.logger.info(f'Post request {route}')
		# assemble address and header
		addr = f"{self.modio_api_url}/{route}"
		head = {'Authorization': f'Bearer {self.modio_api_token}', 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
		# send request
		response = requests.post(addr, params=params, headers=head)
		# convert the response to a json dict
		if ret_json == True:
			d = response.json()
			if 'error' in d.keys():
				self.logger.error(f"response containted error {d['error']['code']}, {d['error']['message']}")
				return f"error{d['error']['code']}"

		if ret_json:
			return d
		else:
			return response
	
	
	# make a delete request to modio
	#	route = address to make request at (ex. games/3959/mods)
	def modio_delete(self, route):
		self.logger.info(f'Delete request {route}')
		# assemble address and header
		addr = f"{self.modio_api_url}/{route}"
		head = {'Authorization': f'Bearer {self.modio_api_token}', 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
		# send request
		response = requests.delete(addr, params={}, headers=head)

		return response
	
	# get an image from modio
	#	route = image address acquired from a mod message
	def get_modio_image(self, route):
		self.logger.info(f'Get modio image {route}')
		# assemble address and header
		# addr = f"{self.modio_api_url}/{route}"
		head = {'Authorization': f'Bearer {self.modio_api_token}', 'Content-Type': 'application/x-www-form-urlencoded', 'Accept': 'application/json'}
		# send request
		response = requests.get(route, params={}, headers=head)

		if response.status_code != 200:
			return None
		return response.content
	
	# rate a mod on modio
	def modio_rate_mod(self, ugc, like=False, dislike=False):
		resp = None
		if like:
			resp = self.modio_post(f'games/{self.pavlov_gameid}/mods/{ugc}/ratings', params={'rating':1}, ret_json=False)
		elif dislike:
			resp = self.modio_post(f'games/{self.pavlov_gameid}/mods/{ugc}/ratings', params={'rating':-1}, ret_json=False)
		else:
			resp = self.modio_post(f'games/{self.pavlov_gameid}/mods/{ugc}/ratings', params={'rating':0}, ret_json=False)

		if resp:
			if resp.status_code == 404:
				return False
			return True
		return False
		
	# get the user ratings from modio and strip it of non-pavlov games
	def get_modio_user_ratings(self):
		resp = self.modio_get(f'me/ratings', ret_json=False)
		if resp.status_code != 200:
			return {}
		else:
			decoded_cont = resp.json()
			rating_dict = {}
			for item in decoded_cont["data"]:
				if item['game_id'] == int(self.pavlov_gameid):
					rating_dict[item['mod_id']] = item['rating']
			return rating_dict
		
	# get the user ratings from modio and strip it of non-pavlov games
	def get_mod_dependencies(self, ugc):
		resp = self.modio_get(f'games/{self.pavlov_gameid}/mods/{ugc}/dependencies?recursive=true', ret_json=False)
		if resp.status_code != 200:
			return []
		else:
			decoded_cont = resp.json()
			mods = []
			for m in decoded_cont["data"]:
				new_dependancy = {
					'id':m['mod_id'], 
					'name':m['name'],
					'name_id':m['name_id'], 
					# 'maker':m['submitted_by']['username'], 
					'date_added':m['date_added'], 
					# 'date_updated':m['date_updated'], 
					# 'date_live':m['date_live'], 
					# 'description':m['description_plaintext'],
					# 'type':m['tags'][0]['name'],	# may need to expand on this, havent seen a map with more than one tag yet
					# 'logo':m['logo']['thumb_320x180'], #['thumb_640x360'] ['thumb_1280x720']
					# 'dependencies': m['dependencies'],
				}
				mods.append(new_dependancy)
			return mods

	# get the full modlist for Pavlov
	def get_pavlov_modlist(self):
		self.logger.info(f'Getting Pavlov modlist')
		mods = []
		init_resp = self.modio_get(f'games/{self.pavlov_gameid}/mods?_limit=100')
		if 'error' in init_resp:
			return init_resp
		
		resp_result_tot = init_resp['result_total']
		resp_result_cnt = init_resp['result_count']

		if resp_result_tot == 0 or resp_result_cnt == 0:
			self.logger.info(f'No result: total = {resp_result_tot}, count = {resp_result_cnt}')
			return f'errorno mods found'
		
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
				'description':m['description_plaintext'],
				'type':m['tags'][0]['name'],	# may need to expand on this, havent seen a map with more than one tag yet
				'logo':m['logo']['thumb_320x180'], #['thumb_640x360'] ['thumb_1280x720']
				'dependencies': m['dependencies'],
				'modfile':{
					'id': modfile_live_win,
					'date_added':m['modfile']['date_added'],
					'filesize':m['modfile']['filesize'], 	# bytes
					'filehash':m['modfile']['filehash'],
					'version':m['modfile']['version'],
					'binary_url':m['modfile']['download']['binary_url'],
				},
			}

		# go through response and make/add entrys to the mods arr
		for m in init_resp['data']:
			try:
				entry = make_entry(m)
			except:
				self.logger.exception('Error making mod')
				self.logger.error(f'Mod {m}')
				continue
			if entry != None:
				mods.append(entry)
			

		# calculate number of pages to get all users subscribed mods
		total_pages = int(resp_result_tot/resp_result_cnt)+1

		# iter through pages calculated
		for i in range(1,total_pages):
			# get new response (but paginated)
			resp = self.modio_get(f'games/{self.pavlov_gameid}/mods?_offset={int(i*100)}&_limit=100')
			if 'error' in resp:
				return resp
			# go through response and make/add entrys to the mods arr
			for m in resp['data']:
				entry = make_entry(m)
				if entry != None:
					mods.append(entry)
				
		return mods
	

	# get the full subscription list of the user 
	# returns a dictionary entry for each subscribed mod with attributes listed below
	def get_subscribed_modlist(self):
		self.logger.info(f'Getting subscribed modlist')
		mods = []
		# get initial subscribed mods for pavlov (first 100 entrys)
		init_resp = self.modio_get(f'me/subscribed?game_id={self.pavlov_gameid}&_limit=100')
		if 'error' in init_resp:
			return init_resp

		resp_result_tot = init_resp['result_total']
		resp_result_cnt = init_resp['result_count']

		if resp_result_tot == 0 or resp_result_cnt == 0:
			self.logger.info(f'No result: total = {resp_result_tot}, count = {resp_result_cnt}')
			return f'errorno subscribed mods found'

		# create a dict to enter into the mods folder
		def make_entry(m):
			modfile_live_win = None
			for p in m['platforms']:
				# only use downloads for the target operating system
				if p['platform'] == self.target_os:
					modfile_live_win = p['modfile_live']
			
			if modfile_live_win == None:
				return None
			
			# modfile_details = None
			# for d in m['modfile']:
			# 	if d['platforms']:

			# attributes in a subscribed modlist entry
			return {
				'id':m['id'], 
				'name':m['name'],
				'name_id':m['name_id'], 
				'maker':m['submitted_by']['username'], 
				'date_added':m['date_added'], 
				'date_updated':m['date_updated'], 
				'date_live':m['date_live'], 
				'description':m['description_plaintext'],
				'type':m['tags'][0]['name'],	# may need to expand on this, havent seen a map with more than one tag yet
				'logo':m['logo']['thumb_320x180'], #['thumb_640x360'] ['thumb_1280x720']
				'dependencies': m['dependencies'],
				'modfile':{
					'id': modfile_live_win,
					'date_added':m['modfile']['date_added'],
					'filesize':m['modfile']['filesize'], 	# bytes
					'filehash':m['modfile']['filehash'],
					'version':m['modfile']['version'],
					'binary_url':m['modfile']['download']['binary_url'],
				},
			}

		# go through response and make/add entrys to the mods arr
		for m in init_resp['data']:
			entry = make_entry(m)
			if entry != None:
				mods.append(entry)

		# calculate number of pages to get all users subscribed mods
		total_pages = int(resp_result_tot/resp_result_cnt)+1

		# iter through pages calculated
		for i in range(1,total_pages):
			# get new response (but paginated)
			resp = self.modio_get(f'me/subscribed?game_id={self.pavlov_gameid}&_offset={int(i*100)}&_limit=100')
			if 'error' in resp:
				return resp
			# go through response and make/add entrys to the mods arr
			for m in resp['data']:
				entry = make_entry(m)
				if entry != None:
					mods.append(entry)
				
		return mods
	
	# remove items from a directory path
	def remove_items_from_dir(self, dirpath, rm_dir=False):
		try:
			files_to_remove = []
			folders_to_remove = []
			for path, folders, files in os.walk(dirpath):
				for f in files:
					files_to_remove.insert(0,f'{path}/{f}')
				for f in folders:
					folders_to_remove.insert(0,f'{path}/{f}')

			for file in files_to_remove:
				os.remove(file)
			for folder in folders_to_remove:
				os.rmdir(folder)

			if rm_dir:
				os.rmdir(dirpath)
		except Exception as e:
			self.logger.exception(f'Exception when removing mod folders')
			self.logger.info(f'Skipped removing dir items : {e}')
	
	# get a list of installed mods (from Pavlov mod directory)
	# returns a dictionary of UGC codes and versions (taint file contents) (ex. {'UGC3262677': 4333298,...})
	def get_installed_modlist(self):
		self.logger.info(f'Getting installed modlist')
		mods = {}
		# iter through pavlov mod directory
		for path, folders, files in os.walk(self.pavlov_mod_dir_path):
			# iter through folders to get UGC of each mod in the folder
			for folder in folders:
				if 'UGC' in folder:
					try:	# attempt to convert folder into UGC int, may fail if folder contains 'UGC' but not modfolder
						ugc = int(folder.strip('UGC'))
					except:	# not a Pavlov mod folder
						self.logger.exception(f'Exception when getting installed mods')
						self.logger.error(f'Occured with mod {ugc}')
						continue

					# also try to read the 'taint' file (where the version is stored)
					version = None
					os.path.join(path, folder, 'taint')

					# get the path to the taint file and see if it exists, if no taint file the next part will fail
					taint_path = f'{path}/{folder}/taint'
					if not os.path.exists(taint_path):
						self.remove_items_from_dir(f'{path}/{folder}', rm_dir=True)
						continue

					try:
						with open(f'{path}/{folder}/taint', 'r') as t:
							text = t.read()
							if text != '':
								version = int(text)
							else:
								continue

						if version != None:
							mods[ugc] = version

					except:
						self.logger.exception(f'Exception when getting installed mods')
						self.logger.error(f'Occured with mod {ugc}')
						continue
			break	# only look at initial folder, dont use recursive os.walk functionality

		return mods
	
	# download a mod file from mod.io
	#	ugc = UGC code of the map to download
	#	version = version id of the map version that will be installed
	#	code_to_run_during_download = optional function call to replace code executed during mod download (for a progress bar)
	def download_modio_file(self, ugc, version, code_to_run_during_download=None):
		self.logger.info(f'Downloading modio file')
		ugc_path = f'{self.pavlov_mod_dir_path}/UGC{ugc}'
		tempfile_path = None
		try:
			# got file info
			# code to support gui
			if code_to_run_during_download != None:
				code_to_run_during_download(0, -3)

			# get mod file information
			resp = self.modio_get(f'games/3959/mods/{ugc}/files/{version}')
			if 'error' in resp:
				return resp
			
			# got file info
			# code to support gui
			if code_to_run_during_download != None:
				code_to_run_during_download(0, -2)

			# check the virus status of the file
			if resp['virus_positive'] != 0:
				self.logger.info(f'Virus detected, skipping')
				return 'Virus detected by Mod.io in modfile'

			# made dir
			# code to support gui
			if code_to_run_during_download != None:
				code_to_run_during_download(0, -1)

			# this code segment is from this site: https://www.alpharithms.com/progress-bars-for-python-downloads-580122/
			# use a context manager to make an HTTP request and file
			import sys, time
			head = {'Authorization': f'Bearer {self.modio_api_token}', 'Accept': 'application/json'}
			
			if code_to_run_during_download == None:
				self.logger.info(f'Making request to Mod.io')

			# make the request
			with requests.get(resp['download']['binary_url'], headers=head, stream=True) as r:
				# tell gui the download has begun
				# code to support gui
				if code_to_run_during_download != None:
					code_to_run_during_download(0, 0)
				else:
					self.logger.info('Downloading mod')

				last_c = 1	# counter for gui update
				last_std_write = 0 # counter for print() update
				with tempfile.NamedTemporaryFile(delete=False) as file:
					tempfile_path = file.name
					# Get the total size, in bytes, from the response header
					total_size = int(r.headers.get('Content-Length'))
					if total_size == 0:
						return 'No file content'
					# Define the size of the chunk to iterate over (Mb)
					chunk_size = 1000
					# iterate over every chunk and calculate % of total
					for i, chunk in enumerate(r.iter_content(chunk_size=chunk_size)):
						file.write(chunk)
						# calculate current percentage
						c = i * chunk_size / total_size * 100
						# code to support gui
						if code_to_run_during_download != None:
							if c+1 > last_c:
								last_c += 1
								code_to_run_during_download(total_size/1e6, c)
						else:
							# write current % to console, pause for .1ms, then flush console
							if c > last_std_write+0.1:
								last_std_write = c
								sys.stdout.write(f"\r{round(c, 1)}%")
								sys.stdout.flush()


					# write 100% to the terminal
					if code_to_run_during_download == None:
						sys.stdout.write(f"\r100.0%\n")
						sys.stdout.flush()
			
			# tell the gui the download is complete
			if code_to_run_during_download != None: 
				code_to_run_during_download(0, 100.0)


			# check if the mod directory exists
			if os.path.exists(ugc_path):
				# iter through the UGC folder to delete files/folders
				self.remove_items_from_dir(ugc_path)
					
			# if the directory doesnt exist, make the directory
			else:
				os.mkdir(f'{self.pavlov_mod_dir_path}/UGC{ugc}')
			# make the Data directory
			os.mkdir(f'{self.pavlov_mod_dir_path}/UGC{ugc}/Data')

			try:
				# unzip the downloaded file and place it in the Data directory
				with zipfile.ZipFile(tempfile_path, 'r') as z:
					z.extractall(f"{self.pavlov_mod_dir_path}/UGC{ugc}/Data/")
			except:
				self.logger.exception(f'Exception installing mod')

			# open the 'taint' file and write the new version
			with open(f'{self.pavlov_mod_dir_path}/UGC{ugc}/taint', 'w') as f:
				f.write(f'{version}')

			# remove temp file
			os.remove(tempfile_path)
				
			return True
		
		except Exception as e:
			self.logger.exception(f'Exception installing mod')
			self.logger.info(e)
			self.logger.info(f'Could not install mod, skipping')
			# if transferring the file/writing taint file fails, remove the mod dir for clean install next time
			self.remove_items_from_dir(ugc_path, rm_dir=True)

			if tempfile_path != None:
				if os.path.exists(tempfile_path):
					os.remove(tempfile_path)
			return e

	# find miscomparisons between modio latest mod versions and installed mod versions
	#	subscribed_list = list of subscribed mod files (expects output from get_subscribed_modlist())
	#	installed_list = list of installed mod files (expects output from get_installed_modlist())
	# todo: make another api call and pull the latest installed-but-not-installed mods data (individual calls or batch?)
	def find_miscompares_in_modlists(self, subscribed_list, installed_list, printout=True):
		self.logger.info(f'Finding miscompares')
		miscompares = []
		not_installed = []
		not_subscribed = []
		subscribed_ids = []
		# print table header and iter mods in subscribed_list
		if printout:
			self.logger.info(f'Status     |  {"Map Name":50s}  | UGC        | Version (modio : installed)')
		for item in subscribed_list:
			# add id to subscribed ids (used for not_subscribe arr assembly)
			subscribed_ids.append(item['id'])
			# check if the ugc from the sub_modlist is in installed_list
			if item['id'] in installed_list:
				# compare the version from mod.io against the taint file version
				if item['modfile']['id'] == installed_list[item['id']]:
					if printout:
						self.logger.info(f'Up to date | "{item["name"]:50s}" | UGC{item["id"]} | {item["modfile"]["id"]} == {installed_list[item["id"]]}')
				else:
					if printout:
						self.logger.info(f'Mismatch in id | "{item["name"]:46s}" | UGC{item["id"]} | {item["modfile"]["id"]} != {installed_list[item["id"]]}')
					# add to miscompare arr since it is different from the latest version
					miscompares.append(item)
			else:
				if printout:
					self.logger.info(f'Mod not installed | {" ":43s} | UGC{item["id"]}')
				# add to not_installed arr since id is not installed
				not_installed.append(item)
		
		# check if all installed keys are part of user subscriptions
		for inst_key in installed_list.keys():
			if inst_key not in subscribed_ids:
				not_subscribed.append(inst_key)

		self.logger.info(f'Mis: {len(miscompares)}, Not Inst: {len(not_installed)}, Not Sub: {len(not_subscribed)}')

		return miscompares, not_installed, not_subscribed
	
	# update the mods installed in pavlov mod directory
	def update_subscribed_mods(self):
		self.logger.info(f'Updating subscribed mods')
		# get list of subscribed mods
		subs_list = self.get_subscribed_modlist()
		if 'error' not in subs_list:
			self.logger.info(f"=== There are {len(subs_list)} subscribed mods ===")
		else:
			self.logger.info('Could not get subscribed mods')
			os._exit(1)

		# get list of installed mods
		installed_mods = self.get_installed_modlist()
		if len(installed_mods) > 0:
			self.logger.info(f"=== There are {len(subs_list)} subscribed mods ===")
		else:
			self.logger.info('Could not get installed mods')
			os._exit(1)

		# find mods that are 1) not latest version, 2) not installed, 3) installed but not subscribed
		miscompares, not_installed, not_subscribed = self.find_miscompares_in_modlists(subs_list, installed_mods)
		
		self.logger.info(f'Miscompared: {len(miscompares)}, Not Installed: {len(not_installed)}, Not Subscribed: {len(not_subscribed)}')
		
		# if there are miscompares, download the latest version
		if len(miscompares) > 0:
			self.logger.info(f'=== Updating out of date mods ===')
			for mod in miscompares:
				self.logger.info(f'-- Updating {mod["name"]} --')
				self.download_modio_file(mod['id'], mod['modfile']['id']) 
			pass

		# if there are mods not installed, download the latest version
		if len(not_installed) > 0:
			self.logger.info(f'=== Installing not-yet installed mods ===')
			for mod in not_installed:
				self.logger.info(f'-- Installing {mod["name"]} --')
				self.download_modio_file(mod['id'], mod['modfile']['id']) 
			pass 

		# if there are mods downloaded but are not subscribed to, post subscription request
		if len(not_subscribed) > 0:
			self.logger.info(f'=== Subscribing to not-yet subscribed mods ===')
			for modid in not_subscribed:
				self.logger.info(f'-- Subscribing to UGC{modid} --')
				resp = self.modio_post(f'games/{self.pavlov_gameid}/mods/{modid}/subscribe')
				mod_dependencies = self.get_mod_dependencies(modid)
				for dependency in mod_dependencies:
					self.logger.info(f'-- Subscribing to UGC{dependency["id"]} (dependency of {modid} --')
					resp = self.modio_post(f'games/{self.pavlov_gameid}/mods/{dependency["id"]}/subscribe', ret_json=False)
			pass

if __name__ == "__main__":
	import logging
	import sys

	logging.basicConfig(filename="pypavlovupdater.log",
						format='%(asctime)s %(message)s',
						filemode='w+')
	logger = logging.getLogger()
	logger.addHandler(logging.StreamHandler(sys.stdout))

	logger.setLevel(logging.INFO)
	# logger.setLevel(logging.ERROR)

	logger.info(f'PyPavlovUpdater Version {major_vers}.{minor_vers}\n')

	# use the configuration manager to load configuration variables from the .conf file
	import settings_manager

	conf_dict = None
	cm = settings_manager.Conf_Manager('PPU.conf', logger)
	if os.path.exists('PPU.conf'):
		conf_dict = cm.get_file_conts_as_dict()

	# file doesnt exist so make a new file
	else:
		logger.info('PPU.conf does not exist, creating file')
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
					logger.info(f'Invalid API token input')
					modio_api_token_input = None
		except:
			logger.exception(f'Exception when attempting to get token')
			logger.info(f'Canceled attempt to enter API token')
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
					logger.info(f'Invalid Pavlov directory input')
					pavlov_mod_dir_path_input = None
		except:
			logger.exception(f'Exception when attempting to get mod path')
			logger.info(f'Canceled attempt to enter mod path')
	else:
		dir_ok = True

	# update the configuration if either the API or mod dir have changed
	if update:
		os.remove('PPU.conf')
		cm.make_new_conf_file(conf_dict['modio_api_token'], conf_dict['pavlov_mod_dir_path'])
	
	# check if there is an API string and mod directory path
	if api_ok and dir_ok:
		# create pavlov updater object
		pu = PavlovUpdater(pavlov_mod_dir_path=conf_dict['pavlov_mod_dir_path'], modio_api_token=conf_dict['modio_api_token'], logging_obj=logger)
		# get all subscribed modes
		logger.info(f'Updating subscribed mods')
		pu.update_subscribed_mods()
	
		logger.info('=== Finished Updating ===')