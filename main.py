import requests
import json
from scipy import stats
import yaml

'''
Pull a Users collection log data
Take that data and clean it up (removing unused fields, etc)
Calculate overall dryness at each boss
Rank them from dryest to least dry
Show data in a tabular format

Query dryness at specific boss with a formatted chat command

IDEAS:
Going to need a how to guide for how users can begin using this (how to setup clog plugin and export data)

Probably want to schedule a background task with the bot to fetch all the clan user data once per day / every 12 hours
since it will take quite a bit

Show top 3 dryest of all time for each item maybe, as well as current dry people

Combined highscores, HCIM only highscores, Ironman only highscores, and normie highscores (use python tabletoascii package)

'''


class DrynessCalc:
    def __init__(self):
        self.config = {}
        self.clan_id = None
        self.clan_name = ""
        self.clan_members = []
        self.wom_clans_url = ""
        self.wom_clan_members_url = ""
        self.clog_user_url = ""
        # self.highscores_url = "https://secure.runescape.com/m\=hiscore_oldschool/index_lite.json\?player\="

        self.setup()

    def setup(self):
        self.load_config()
        self.clan_name = self.config['clan_name']
        self.wom_clans_url = self.config['urls']['wom_get_clan']
        self.wom_clan_members_url = self.config['urls']['wom_get_clan_members']
        self.clog_user_url = self.config['urls']['clog_api_user']

        self.get_clan_id()
        self.wom_clan_members_url = f"{self.wom_clan_members_url}/{self.clan_id}"

        self.get_clan_member_list()

    def load_config(self) -> None:
        with open('config.yaml', 'r') as f:
            self.config = yaml.load(f, Loader=yaml.SafeLoader)

    @staticmethod
    def read_json(fp: str) -> dict:
        with open(fp, "r") as f:
            data = json.load(f)
        return data

    def get_clan_id(self):
        response = requests.get(url=f"{self.wom_clans_url}?name={self.clan_name}").json()
        self.clan_id = response[0]['id']

    def get_clan_member_list(self) -> None:
        response = requests.get(url=self.wom_clan_members_url).json()

        for member in response['memberships']:
            self.clan_members.append(member['player']['username'])

    def get_user_clog(self, username: str) -> dict:
        response = requests.get(url=f'{self.clog_user_url}/{username}').json()
        return response

    # def get_user_highscores(self, username: str) -> dict:
    #     response = requests.get(url=f"{self.highscores_url}{username}")
    #     return response

    @staticmethod
    def get_user_skill_xp(skill_name: str, highscores: dict) -> int:
        for skill in highscores['skills']:
            if skill['name'] == skill_name:
                return skill['xp']

    def load_bosses(self) -> dict:
        drops = self.read_json(fp="bosses.json")
        return drops

    def calculate_dryness(self, num_success: int, num_attempts: int, drop_chance: float) -> float:
        dryness = stats.binom.pmf(num_success, num_attempts, drop_chance) * 100

        return dryness

    def print_dryness(self, dryness: float, item: str, kills: int, num_drops: int) -> None:
        print("You had a {:.4f}% chance to get {} {}s in {} kills. ".format(dryness, num_drops, item, kills))


if __name__ == '__main__':
    calc = DrynessCalc()

    # boss_rates = calc.load_bosses()
    #
    # smold_rate = boss_rates['Cerberus']['Smouldering stone']
    #
    # users = ["Snape Grass", "Frank Donner", "GimPoutine"]
    # user_clog = calc.get_user_clog(username=user)
    #
    # cerb_kills = user_clog['collectionLog']['tabs']['Bosses']['Cerberus']['killCount'][0]['amount']
    # uniques = {}
    #
    # tracked_drops = boss_rates['Cerberus'].keys()
    #
    # for item in user_clog['collectionLog']['tabs']['Bosses']['Cerberus']['items']:
    #     if item['name'] in tracked_drops:
    #         uniques[item['name']] = item['quantity']
    #
    # total_uniques = 0
    # chance_for_any = 0
    #
    # for key in boss_rates['Cerberus'].keys():
    #     dryness = calc.calculate_dryness(num_success=uniques[key], num_attempts=cerb_kills,
    #                                      drop_chance=boss_rates['Cerberus'][key])
    #     calc.print_dryness(dryness=dryness, item=key, kills=cerb_kills, num_drops=uniques[key])
    #
    #     if key == "Hellpuppy":
    #         continue
    #     elif key == "Jar of souls":
    #         continue
    #     else:
    #         total_uniques += uniques[key]
    #         chance_for_any += boss_rates['Cerberus'][key]
    #
    # dryness = calc.calculate_dryness(num_success=total_uniques, num_attempts=cerb_kills,
    #                                  drop_chance=chance_for_any)
    # calc.print_dryness(dryness=dryness, item="uniques", kills=cerb_kills, num_drops=total_uniques)
