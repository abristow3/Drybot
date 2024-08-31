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
        self.boss_rates = {}
        self.dryest_members = {}

        self.setup()

    def setup(self):
        self.load_config()
        self.boss_rates = self.load_bosses()
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

    def calc_dryest(self):

        dryest = self.read_json(fp="dryness.json")
        self.clan_members = ["Snape Grass", "GimPoutine"]
        first = True

        for member in self.clan_members:
            clog = self.get_user_clog(username=member.lower())

            cerb_kills = clog['collectionLog']['tabs']['Bosses']['Cerberus']['killCount'][0]['amount']

            for unique in self.boss_rates['Cerberus']['uniques'].keys():
                for item in clog['collectionLog']['tabs']['Bosses']['Cerberus']['items']:
                    if item['name'] == unique:
                        # Calculate dryness
                        dryness = self.calculate_dryness(num_success=item['quantity'], num_attempts=cerb_kills,
                                                         drop_chance=self.boss_rates['Cerberus']['uniques'][
                                                             item['name']])

                        if first:
                            dryest['Cerberus']['uniques'][unique]['dryness'] = dryness
                            dryest['Cerberus']['uniques'][unique]['player'] = member
                        elif dryness < dryest['Cerberus']['uniques'][unique]['dryness']:
                            dryest['Cerberus']['uniques'][unique]['dryness'] = dryness
                            dryest['Cerberus']['uniques'][unique]['player'] = member
                        else:
                            continue

                        # self.print_dryness(dryness=dryness, item=item['name'], kills=cerb_kills, num_drops=item['quantity'])

            if first:
                first = False

        print(json.dumps(dryest['Cerberus'], indent=4))

        '''
        Get list of clan members
        for each clan member get their clog
        calc how dry they are for each unique
        
        make a copy of the bosses.json file and replace the boss rates with a lsit of "playername:dryness"
        sort the lsit by appending on the : and sort by rate?
        
        '''

    def load_bosses(self) -> dict:
        drops = self.read_json(fp="bosses.json")
        return drops

    def calculate_dryness(self, num_success: int, num_attempts: int, drop_chance: float) -> float:
        dryness = stats.binom.pmf(num_success, num_attempts, drop_chance) * 100

        return dryness

    def print_dryness(self, dryness: float, item: str, kills: int, num_drops: int) -> None:
        print("You had a {:.4f}% chance to get {} {}s in {} kills. ".format(dryness, num_drops, item, kills))


    def dry_dict(self):
        dryest = {}
        for boss in self.boss_rates.keys():
            dryest[boss] = {}
            dryest[boss]["uniques"] = {}
            print(self.boss_rates[boss]['uniques'].keys())
            for item in self.boss_rates[boss]['uniques'].keys():
                dryest[boss]["uniques"][item] = {"player": "", "dryness": ""}

        with open("dryness.json", 'w') as f:
            json.dump(dryest, f)


if __name__ == '__main__':
    calc = DrynessCalc()
    calc.calc_dryest()

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
