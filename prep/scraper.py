from selenium import webdriver
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import pandas as pd
import tabula as tb
import pickle

options = FirefoxOptions()
options.add_argument('--no-sandbox')
options.add_argument("--headless")
options.add_argument('--disable-gpu')
options.add_argument('--disable-dev-shm-usage')
options.add_argument("--window-size=1920,1080")
driver = webdriver.Firefox(executable_path=r"C:\Users\rgrie\PycharmProjects\geckodriver.exe", options=options)

url = 'https://www.handball4all.de/home/portal/hhhvsh#/league?ogId=77&lId=77611&allGames=1'

driver.get(url)

ls_mHSOL_ab = driver.find_elements(by=By.CLASS_NAME, value='ng-scope')
ls_mHSOL_ab = [x.get_attribute('ng-href') for x in ls_mHSOL_ab]
ls_mHSOL_ab = [x for x in ls_mHSOL_ab if x is not None]


with open(r"C:\Users\rgrie\PycharmProjects\handball-stats\data\220316_ls_mHSOL_ab", 'wb') as fp:
    pickle.dump(ls_mHSOL_ab, fp)

driver.close()



def get_game_info(file):
    game_title = tb.read_pdf(file, area=(50, 50, 100, 500), pages='1')[0]
    txt = game_title.iloc[0, 0].split()
    league = txt[0]
    game_nr = txt[3]

    game_info = tb.read_pdf(file, area=(80, 50, 200, 500), pages='1')[0]
    date_txt = game_info.iloc[0, 1].split(" am ")
    date_txt = date_txt[1].split(" um ")
    date = date_txt[0]
    loc_txt = game_info.iloc[1, 1].split()
    loc_txt = [x for x in loc_txt if "(1" in x]
    location = loc_txt[0][1:-1]
    teams_txt = game_info.iloc[2, 1].split(" - ")
    team1 = teams_txt[0]
    team2 = teams_txt[1]

    return league, game_nr, date, location, team1, team2


def get_teams(file):
    team_one = tb.read_pdf(file, area=(150, 50, 400, 880), pages='2', lattice=True)[0]

    team_two = tb.read_pdf(file, area=(435, 50, 800, 880), pages='2', lattice=True)[0]

    players_t1 = team_one["Name"].unique().tolist()
    players_t1 = [x for x in players_t1 if x == x]

    players_t2 = team_two["Name"].unique().tolist()
    players_t2 = [x for x in players_t2 if x == x]

    return players_t1, players_t2


def get_report(file):
    data_page_three = tb.read_pdf(file, area=(100, 50, 800, 500), pages='3', lattice=True)[0]
    data_page_three.columns = ["Zeit", "Spielzeit", "Stand", "Aktion"]
    data_page_four = \
    tb.read_pdf(file, area=(50, 50, 800, 500), pages='4', lattice=True, pandas_options={'header': None})[0]
    data_page_four.columns = ["Zeit", "Spielzeit", "Stand", "Aktion"]

    df_report = pd.concat([data_page_three, data_page_four])

    return df_report


def get_stats(df_report, league, game_nr, game_date, location, team1, team2, players_t1, players_t2):
    stats = []
    # verlauf = df_report["Aktion"].tolist()
    for i in range(len(df_report)):
        txt = df_report.iloc[i, 3]
        for player in players_t1:
            if "Tor" in txt and player in txt and "KEIN" not in txt and "7m" not in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team1, df_report.iloc[i, 1], 1, 0, 0,
                     0, 0, 0, 0])
            if "7m-Tor" in txt and player in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team1, df_report.iloc[i, 1], 1, 0, 1,
                     0, 0, 0, 0])
            if "7m" in txt and "KEIN" in txt and player in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team1, df_report.iloc[i, 1], 0, 1, 1,
                     0, 1, 0, 0])
            if "Verwarnung" in txt and player in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team1, df_report.iloc[i, 1], 0, 0, 0,
                     1, 0, 0, 0])
            if "2-min" in txt and player in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team1, df_report.iloc[i, 1], 0, 0, 0,
                     0, 1, 0, 0])

        for player in players_t2:
            if "Tor" in txt and player in txt and "KEIN" not in txt and "7m" not in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team2, df_report.iloc[i, 1], 1, 0, 0,
                     0, 0, 0])
            if "7m-Tor" in txt and player in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team2, df_report.iloc[i, 1], 1, 0, 1,
                     0, 0, 0])
            if "7m" in txt and "KEIN" in txt and player in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team2, df_report.iloc[i, 1], 0, 1, 1,
                     0, 1, 0])
            if "Verwarnung" in txt and player in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team2, df_report.iloc[i, 1], 0, 0, 0,
                     1, 0, 0])
            if "2-min" in txt and player in txt:
                stats.append(
                    [league, game_nr, location, game_date, team1, team2, player, team2, df_report.iloc[i, 1], 0, 0, 0,
                     0, 1, 0])

        if "Auszeit" in txt and str(team1) in txt:
            stats.append(
                [league, game_nr, location, game_date, team1, team2, "timeout", team1, df_report.iloc[i, 1], 0, 0, 0, 0,
                 0, 0, 1])
        if "Auszeit" in txt and str(team2) in txt:
            stats.append(
                [league, game_nr, location, game_date, team1, team2, "timeout", team2, df_report.iloc[i, 1], 0, 0, 0, 0,
                 0, 0, 1])

    return stats

# Read Input
with open (r"C:\Users\rgrie\PycharmProjects\handball-stats\data\220316_ls_mHSOL_ab", 'rb') as fp:
    ls_mHSOL_ab = pickle.load(fp)

# Create List
all_stats = []

for file in ls_mHSOL_ab:
    try:
        league, game_nr, date, location, team1, team2 = get_game_info(file)
        df = get_report(file)

        players_t1, players_t2 = get_teams(file)

        # append stats
        stats = get_stats(df, league, game_nr, date, location, team1, team2, players_t1, players_t2)
        all_stats.extend(stats)
    except FileNotFoundError: print("No such file")

columns = ["league", "game_nr", "location", "game_date", "home", "guest", "player","team", "time", "goal", "missed", "7m", "yellow", "2min", "red", "timeout"]
df_stats = pd.DataFrame(all_stats, columns=columns)


df_stats.to_csv(r"C:\Users\rgrie\PycharmProjects\handball-stats\data\220316_ls_mHSOL_ab.csv", index=False)

