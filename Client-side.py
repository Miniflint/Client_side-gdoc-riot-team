import riotwatcher
from datetime import timedelta
from sys import exit as sys_exit
import time
import socket
from os import path

PORT = 25500
ENCODING = "utf-8"
REGION_SUMMONER = "euw1"
REGION_MATCH = 'europe'
FILENAME_STATS = "game_stats.txt"
VERSION = 1.23

def error_occured(msg, check = False):
	print(f"[Error] : {msg}")
	if (not check):
		print("Please contact Miniflint (Miniflint#0025) for more informations")
	time.sleep(20)
	sys_exit()

class connect_to_server:
	"""Handling connections to server and receiving data"""
	def connect_server(host) -> socket.socket:
		"""Checking connection and connecting to the server"""
		server = socket.gethostbyname(host)
		addr = (server, PORT)
		client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		client.settimeout(7)
		client.connect(addr)
		return client

	def get_msg() -> str:
		"""
		Function to communicate with my server
		
		Get the key from a txt file
		"""
		host_name = ["ubuntu", "startrek.synology.me"]
		print("Finding API KEY from miniflint's server")
		try:
			client = connect_to_server.connect_server(host_name[1])
		except:
			try:
				client = connect_to_server.connect_server(host_name[0])
			except:
				error_occured("Unable to connect to the server")
		api_key = client.recv(128).decode(ENCODING)
		client.send(bytes(str(VERSION), encoding=ENCODING))
		check_version = client.recv(1024).decode(ENCODING)
		if (check_version != ""):
			print(check_version)
		if (api_key):
			if (len(api_key) == 42):
				return api_key
			else:
				error_occured("Wrong riot api key")
		else:
			error_occured("Unable to decode data from the server")

API_KEY = connect_to_server.get_msg()
WATCHER = riotwatcher.LolWatcher(API_KEY)

class get_last_match_infos:
	"""Infos about last match"""
	def get_kda(kill, death, assist):
		"""Calculate KDA"""
		if (kill + assist == 0):
			return 0
		if (death == 0 or death == 1):
			return 100
		kda = (kill + assist) / death
		return str(round(kda, 2))

	def convert_time(timestamp_start:int, timestamp_end:int):
		"""Convert timestamp into human readable format
		
		Get Game time"""
		start_time = time.strftime('%d/%m/%Y %H:%M', time.localtime(timestamp_start / 1000))
		seconds = (timestamp_end - timestamp_start) / 1000
		real_time = str(timedelta(seconds=int(seconds)))
		for_farm = round((seconds / 60), 2)
		return real_time, start_time, for_farm

	def print_all(all):
		"""Write the 2d array in the file"""
		f = open(FILENAME_STATS, "w")
		for x in all:
			for i in x:
				write_data = str(i).replace(".",",")
				f.write(f"{write_data}\t")
			f.write("\n")
		f.close()

	def get_kill_part(player_kill, player_assists, total_kill):
		"""Calculate kill participation"""
		kill_part = ((player_kill + player_assists) / total_kill) * 100
		kill_round = round(kill_part, 2)
		return f"{kill_round}%"

	def get_champ_and_stats(dict_infos:dict, team_infos:dict, game_start, game_duration, game_id, game_time):
		"""Make the 2d Array with a dictionnary\n

		1. name (summoner name 'Miniflint')
		2. game_start (Time at which the game started -> 19.02.2021 19:32)
		3. champ (Champion -> 'Jax')
		4. game_id (Game Id -> EUW1-{numberhere})
		5. kills (Number of kills by the player)
		6. deaths (Number of deaths by the player)
		7. assists (Number of assists by the player)
		8. kda (kills / deaths / assists ratio)
		9. win_or_lose (wether the player won, or not)
		10. kill_part (kill participation in the game)
		11. ward_placed (Number of ward placed)
		12. vision_score (Score of vision by the player)
		13. farm (farm of the player)
		14. cs_per_minute (farm per minute -> farm / 60)
		15. game_duration (How long the game have been going)
		16. total_kill_team (Total kill of the team)

		This is the data collected and stored in the 2d array. for each player
		"""
		stats = []
		for keys in dict_infos:
			# player_champs.append(keys)
			name =			keys['summonerName']
			champ =			keys['championName']
			kills =			keys['kills']
			deaths =		keys['deaths']
			assists =		keys['assists']
			ward_placed =	keys['wardsPlaced']
			vision_score =	keys['visionScore']
			farm =			keys['totalMinionsKilled']
			cs_per_minute =	round(int(farm)/game_time, 2)
			pink_ward = 	keys['sightWardsBoughtInGame']
			kda = f"{get_last_match_infos.get_kda(kills, deaths, assists)}"
			if (keys['win']):
				win_or_lose = "WIN"
			else:
				win_or_lose = "LOSE"
			teamID = keys['teamId']
			for team in team_infos:
				if (teamID == team['teamId']):
					total_kill_team = team['objectives']['champion']['kills']
			kill_part = get_last_match_infos.get_kill_part(kills, assists, total_kill_team)
			stats.append([name, game_start, champ, game_id, kills, deaths, assists, kda, win_or_lose, kill_part, ward_placed, pink_ward, vision_score, farm, cs_per_minute, game_duration, total_kill_team])
		return stats

	def get_last_match(summoners_name, match_nb:int):
		"""Get last match of the desired summoner"""
		try:
			me = WATCHER.summoner.by_name(REGION_SUMMONER, summoners_name)
		except:
			error_occured("Wrong riot api key")
		my_matches = WATCHER.match.matchlist_by_puuid(REGION_MATCH, me['puuid'])
		last_match = my_matches[match_nb]
		match_detail = WATCHER.match.by_id(REGION_MATCH, last_match)
		
		return match_detail, match_detail['metadata']['matchId']

def send_request(summoners_name, match_nb):
	"""Second main. i just had no idea what to call it"""
	print(f"informations about the match of : {summoners_name}...")
	last_match, match_id = get_last_match_infos.get_last_match(summoners_name, match_nb)

	print("Informations about the time of the match...")
	game_duration, time_game_start, csing = get_last_match_infos.convert_time(last_match['info']['gameStartTimestamp'], last_match['info']['gameEndTimestamp'])

	participant = last_match['info']['participants']
	teams = last_match['info']['teams']

	print("informations about the stats of the match...")
	champ_game = get_last_match_infos.get_champ_and_stats(participant, teams, str(time_game_start), str(game_duration), match_id, csing)
	get_last_match_infos.print_all(champ_game)
	return

class file:
	FILENAME = "player.txt"
	def read_file(self):
		nb = 1
		if (path.exists(self.FILENAME)):
			f = open(self.FILENAME, "r", encoding=ENCODING)
			for line in f:
				print(f"{nb}. {line}", end="")
				nb += 1
			print(f"\n{nb}. Others")
			f.close()
			return (nb + 1)
		else:
			error_occured(f"Couldn't find the file : {self.FILENAME}")

	def get_line(self, line_nb):
		f = open(self.FILENAME, "r", encoding=ENCODING)
		try:
			output = f.readlines()[line_nb - 1].strip()
		except:
			output = "Others"
		f.close()
		return output

def main():
	init = file()
	max_line = init.read_file()
	user_input = int(input("Choose a number : "))
	if (user_input > 0 and user_input < max_line):
		name = init.get_line(user_input)
		print(f"You choose : {name}")
		if (user_input == max_line - 1):
			name = input("Enter your league name : ")
	else:
		error_occured("Enter a valable number", True)
	print("Enter a match number (0 -> most recent to 5 -> oldest)")
	match_nb = int(input("Enter a match : "))
	if (match_nb > 6 or match_nb < 0):
		error_occured("Enter a valable number", True)
	send_request(name, match_nb)
	print(f"\nSelect your name ({name}) in this file : {FILENAME_STATS}")
	time.sleep(15)
	sys_exit()

main()
