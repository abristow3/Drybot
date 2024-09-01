import time
import datetime

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

        self.clan_members.sort()

    def get_user_clog(self, username: str):
        response = requests.get(url=f'{self.clog_user_url}/{username}')

        if response.status_code == 200:
            return response.json()
        else:
            return None

    def calc_dryest(self):

        dryest = self.read_json(fp="dryness.json")
        first = True

        for member in self.clan_members:
            clog = self.get_user_clog(username=member.lower())

            print(f"USERNAME: {member}")

            if clog is None:
                print("NO CLOG DATA")
                continue

            print("CLOG DATA")

            for boss in clog['collectionLog']['tabs']['Bosses']:
                kills = clog['collectionLog']['tabs']['Bosses'][boss]['killCount'][0]['amount']

                if boss in self.boss_rates.keys():
                    for unique in self.boss_rates[boss]['uniques'].keys():
                        for item in clog['collectionLog']['tabs']['Bosses'][boss]['items']:
                            if item['name'] == unique:

                                if item['quantity'] != 0:
                                    continue

                                # Calculate dryness
                                dryness = self.calculate_dryness(num_success=item['quantity'], num_attempts=kills,
                                                                 drop_chance=self.boss_rates[boss]['uniques'][
                                                                     item['name']])

                                if first:
                                    dryest[boss]['uniques'][unique]['dryness'] = dryness
                                    dryest[boss]['uniques'][unique]['player'] = member
                                    dryest[boss]['uniques'][unique]['kills'] = kills
                                    dryest[boss]['uniques'][unique]['quantity'] = item['quantity']
                                elif dryness < dryest[boss]['uniques'][unique]['dryness']:
                                    dryest[boss]['uniques'][unique]['dryness'] = dryness
                                    dryest[boss]['uniques'][unique]['player'] = member
                                    dryest[boss]['uniques'][unique]['kills'] = kills
                                    dryest[boss]['uniques'][unique]['quantity'] = item['quantity']
                                else:
                                    continue

            if first:
                first = False

        print(json.dumps(dryest, indent=4))

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
            for item in self.boss_rates[boss]['uniques'].keys():
                dryest[boss]["uniques"][item] = {"player": "", "dryness": "", "kills": "", "quantity": ""}

        with open("dryness.json", 'w') as f:
            json.dump(dryest, f)


if __name__ == '__main__':
    calc = DrynessCalc()

    start = time.time()
    calc.calc_dryest()
    end = time.time()
    total = end - start
    minutes = str(datetime.timedelta(seconds=total))
    print(minutes)

    '''
    total time to run without loop unrolling:
    '''

    # calc.get_user_clog(username="Frank Donner")
    # calc.dry_dict()

    # user_clog = calc.get_user_clog(username=user)
