
# Configuration manager class to process configuration file
# Used to read program settings from a configuration file that can be updated by the user from text editor
class Conf_Manager:
	def __init__(self, fileaddr) -> None:
		self.fileaddr = fileaddr
	
	# strip the additional characters from the values assigned to a variable (generates an array)
	def process_varconts(self, data):
		data = data.split(',')
		out = []
		for val in data:
			out.append(val.strip(' ').strip('"'))
		return out

	# get the file contents from the file as dictionary keys/values that will be returned
	# returns None if file does not exist (or invalid character in the line when processing)
	def get_file_conts_as_dict(self):
		d = {}
		try:
			with open(self.fileaddr, 'r') as f:
				fconts = f.read()
				fconts = fconts.split('\n')
				for line in fconts:
					if '#' in line or line == '':
						continue

					varname, varcont = line.split('=')

					if 'modio_api_token' in varname:
						d['modio_api_token'] = self.process_varconts(varcont)[0]

					if 'pavlov_mod_dir_path' in varname:
						d['pavlov_mod_dir_path'] = self.process_varconts(varcont)[0]
			return d
		except:
			return None
	
	# create a new configuration file 
	# can supply api token and mod dir to write into the configuration before closing it
	# primary means of updating configuration from program, call os.remove('PPU.conf') before using
	def make_new_conf_file(self, modio_api_token=None, pavlov_mod_dir_path=None):
		conf_file = open(self.fileaddr, 'x+')
		print(conf_file)

		conts = f"""# =*=*=*=*=   PyPavlovUpdater.exe   =*=*=*=*=
#
#   A simple python-based Mod.io downloader for the Pavlov-VR game
#
#   Make sure you keep this text file and PyPavlovUpdater.exe in the same installation directory or
#   the app will stop working.
#
#   Below are variables that can be configured (in a pythonic way). 
#   Some variables require only one value, some require more than 1.
#   If more than one value is required, each value must be seperate by a comma.
#   All variable lines can have quotations or apostraphes in them, do not use other special characters.
#
#
#       modio_api_token is the mod.io API token used to read+write data from/to Mod.io
#       A token can be acquired from "https://mod.io/me/access", then copied into the modio_api_token variable
#       Must be a valid API token that is not expired

modio_api_token = "{modio_api_token if modio_api_token != None else ''}"

#       pavlov_mod_dir_path should point to your pavlov mods directory 
#       This must be a valid path in quotes

pavlov_mod_dir_path = "{pavlov_mod_dir_path if pavlov_mod_dir_path != None else ''}"
"""
		conf_file.writelines(conts)
		conf_file.close()

# main (for testing)
if __name__ == "__main__":
	cm = Conf_Manager('PPU.conf')
	print(f'CM file conts: {cm.get_file_conts_as_dict()}')