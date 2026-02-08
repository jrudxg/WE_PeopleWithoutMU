import pywarera
import sys
import os
import json
from datetime import datetime, timezone
from math import floor

class JSONWithCommentsDecoder(json.JSONDecoder):
    def __init__(self, **kw):
        super().__init__(**kw)

    def decode(self, s: str):
        s = '\n'.join(l if not l.lstrip().startswith('//') else '' for l in s.split('\n'))
        return super().decode(s)


if getattr(sys, "frozen", False):   basePath = os.path.dirname(sys.executable)
else:                               basePath = os.path.dirname(os.path.abspath(__file__))

settingsPath = os.path.join(basePath, "Settings.json")

if (os.path.exists(settingsPath)):
    with open(settingsPath, 'r') as file: settings = json.load(file, cls=JSONWithCommentsDecoder)
else:
    settings = {
        "apiToken":                         str(input("Enter your api token: ")),
        "country":                          str(input("Enter a country name (capitalize the first letter): ")),
        "minimumLevel":                     int(input("Enter the minimum level the players should have: ")),
        "maximumLastConnectionInHours":     int(input("Enter the maximal last connection time in hours (use a negative time to not use a maximum time): ")),
        "ignoreBannedUsers":                bool(input("Should banned users be ignored (use true/false): ")),
        "ignorePlayersWhoOwnMUs":           bool(input("Should players who own a MU but are not listed in a MU be ignored (use true/false): "))
    }
    
print("settings: ", settings)

pywarera.update_api_token(settings["apiToken"])
now = datetime.now(timezone.utc)

namesOfPlayersWithoutMU = []
playersWithMU = []

for player in pywarera.get_country_citizens_by_name(settings["country"]):
    if settings["minimumLevel"] > player.level or ( settings["ignoreBannedUsers"] and player.is_banned ): continue

    if (settings["maximumLastConnectionInHours"] >= 0):

        timeDelta = now - datetime.fromisoformat(player.dates.last_connection_at.replace("Z", "+00:00"))
        hoursSinceLastConnection = floor(timeDelta.total_seconds()/3600) # 3600 seconds is one hour

        if settings["maximumLastConnectionInHours"] < hoursSinceLastConnection: continue

    if player.mu: playersWithMU.append(player)
    else:
        if settings["ignorePlayersWhoOwnMUs"]:
            mu = pywarera.wareraapi.mu_get_many_paginated(limit=1, user_id=player.id).execute()
            if mu[0]: continue
            
        namesOfPlayersWithoutMU.append(player.username)
         

print("\n\nThere are {} players without a MU:".format(len(namesOfPlayersWithoutMU)), *namesOfPlayersWithoutMU, sep="\n\t")


from collections import Counter

muCounts = Counter(player.mu for player in playersWithMU)
print("\n\nPlayers are in {} MUs:".format(len(muCounts)))

idToNameDict = dict()

for name, count in muCounts.most_common():
    realName = pywarera.wareraapi.mu_get_by_id(name).execute()["name"]
    idToNameDict[name] = realName

    print(f"\t{realName}: {count}")

print("\n\nThere are {} players with a MU:".format(len(playersWithMU)))
for player in playersWithMU:
    print(f"\t{player.username}: {idToNameDict[player.mu]}")

while input("\nPress anything to close the application: ") is None: {}