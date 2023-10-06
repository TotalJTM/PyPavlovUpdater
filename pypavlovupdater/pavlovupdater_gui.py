import pavlovupdater
import settings_manager
import PySimpleGUI as sg


major_vers = 1
minor_vers = 0

# main menu for the pavlov mod updater
def mainmenu():
	# sg.theme('DarkTeal6')
	sg.theme('DefaultNoMoreNagging')

	options_layout = [  
		[sg.Text('Pavlov Mod Updater ')],
		[sg.Submit(), sg.Cancel()],
	]
	
	all_mods_layout = [
		
	]

	subscribed_layout = [
		
	]

	layout = [
		[sg.TabGroup([[sg.Tab('Subscribed Mods', subscribed_layout), sg.Tab('Pavlov Mods on Mod.io', all_mods_layout), sg.Tab('Options', options_layout)]])]
	]

	window = sg.Window('PyPavlovUpdater', layout)
	while True:
		try:
			event, values = window.read()
		except:
			break

		if event == 'Cancel':
			break
		elif event == sg.WIN_CLOSED:
			break		
		elif event == 'Submit':
			break
		else:
			pass

	window.close()

if __name__ == "__main__":
	print(f'PyPavlovUpdater GUI Version {major_vers}.{minor_vers}')
	
	# launch gui main menu
	mainmenu()