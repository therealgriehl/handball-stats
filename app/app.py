import pandas as pd
import streamlit as st
import altair as alt
import seaborn as sns
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter


# --- Setup Streamlit ---
st.set_page_config(layout="wide")


#df_report = pd.read_csv(r"C:\Users\rgrie\PycharmProjects\handball-stats\data\220316_mHSOL_ab.csv", parse_dates=[3], dayfirst=True)

df_report = pd.read_csv(r"https://raw.githubusercontent.com/therealgriehl/handball-stats/main/data/220316_mHSOL_ab.csv", parse_dates=[3], dayfirst=True)

all_games = df_report["game_nr"].unique().tolist()
all_teams = np.unique(df_report[["home", "guest", "team"]].values)
all_players = df_report["player"].unique().tolist()

st.title("Handball Dashboard")

# --- Wahl der Liga ---

league = st.selectbox("Auswahl der Liga", ["Liga1", "Liga2"])

# --- Prüfen, ob Spieler mit gleichem Namen ---

pl_do = df_report.groupby(["player", "team"]).any()
pl_do.reset_index(inplace=True)
pl_do = pl_do[pl_do["player"] != "timeout"]
full_players = pl_do["player"].tolist()
doubles = [key for key in Counter(full_players).keys() if Counter(full_players)[key]>1]

def double_players(row):
    if row["player"] in doubles:
        row["player"] = str(row["player"]) + str(row["team"])

df_report.apply(lambda x: double_players(x), axis=1)

# --- Allgemeine Variablen/DataFrames ---

# Punkte im Saisonverlauf
games_df = df_report.groupby(["game_nr", "team"])["goal"].sum()
games_df = games_df.reset_index()

wins = []
for game in all_games:
    df = games_df[games_df["game_nr"]==game]
    if df.iloc[0,2] > df.iloc[1,2]:
        wins.append([game, df.iloc[0,1]])
    elif df.iloc[1,2] > df.iloc[0,2]:
        wins.append([game, df.iloc[1,1]])
    elif df.iloc[1, 2] == df.iloc[0, 2]:
        wins.append([game, 'Draw'])

wins_df = pd.DataFrame(wins, columns=["game_nr", "winner"])

merged_df = pd.merge(df_report, wins_df, on="game_nr", how="inner")

points = merged_df.groupby(["game_nr"])["winner", "home", "guest", "game_date"].max()
points = points.reset_index()
points_list = []
for i in range(len(points)):
    if points.iloc[i,1] == "Draw":
        points_list.append([points.iloc[i,0], points.iloc[i,4], points.iloc[i,2], 1, 1])
        points_list.append([points.iloc[i,0], points.iloc[i,4], points.iloc[i, 3], 1, 1])
    elif points.iloc[i,1] in all_teams:
        if points.iloc[i,1] == points.iloc[i,2]:
            points_list.append([points.iloc[i,0], points.iloc[i,4], points.iloc[i, 2], 2, 0])
            points_list.append([points.iloc[i,0], points.iloc[i,4], points.iloc[i, 3], 0, 2])
        if points.iloc[i,1] == points.iloc[i,3]:
            points_list.append(([points.iloc[i,0], points.iloc[i,4], points.iloc[i,3], 2, 0]))
            points_list.append([points.iloc[i,0], points.iloc[i,4], points.iloc[i, 2], 0, 2])
points_df = pd.DataFrame(points_list, columns=["game_nr", "game_date", "team", "points+", "points-"])
points_df = points_df.sort_values(by="game_date")
points_df["sum_points+"] = points_df.groupby("team")["points+"].transform(pd.Series.cumsum)
points_df["sum_points-"] = points_df.groupby("team")["points-"].transform(pd.Series.cumsum)
points_season_df = points_df.groupby("team")[["points+", "points-"]].sum()
points_season_df.reset_index(inplace=True)
# Anzahl Spiele je Team
amount_games = points_df.groupby("team").count()
amount_games = amount_games.reset_index()

amount_games= amount_games.drop(columns=["game_date", "points+", "points-", "sum_points+", "sum_points-"])
amount_games.rename(columns={"game_nr":"amount_games"}, inplace=True)

# Erstelle Tabelle
season_table = amount_games.copy()
season_table = pd.merge(season_table, points_season_df[["team","points+", "points-"]], how="inner", on="team")
# Tore pro Team
teamgoals = df_report.groupby(["team"]).sum().sort_values(by="goal", ascending=False)
teamgoals = teamgoals.reset_index()
teamgoals = pd.merge(teamgoals, amount_games, on="team", how="inner")

# --- Tabelle ---

season_table = pd.merge(season_table, teamgoals[["team","goal"]], on="team", how="inner")
season_table.index = season_table.index + 1
season_table.rename(columns={"team":"Mannschaft",
                            "amount_games":"Spiele",
                             "points+":"Punkte +",
                             "points-": "Punkte -",
                             "goal":"Tore"},
                    inplace=True)
season_table.sort_values(by="Punkte +", ascending=False, inplace=True)
st.caption("Tabelle")
st.table(season_table)

# --- Team Punkte in der Saison ---
fig_teams = px.line(points_df,
                    x="game_date",
                    y="sum_points+",
                    color="team",
                    markers=True,
                    title="Punkte im Saisonverlauf",
                    labels={
                        "game_date":"Datum",
                        "sum_points+":"Anzahl Punkte"
                    })
fig_teams.update_yaxes(tick0=0, dtick=2)
fig_teams.update_layout(legend_title_text='Mannschaften')
st.plotly_chart(fig_teams, use_container_width=True)

# --- Start der Spalten ---

left_column, right_column = st.columns(2)

# --- Tore pro Team ---
fig_tt = px.bar(teamgoals, x="team", y="goal",
                   title="Tore pro Team",
                   labels={
                       "team":"Mannschaft",
                       "goal":"Geworfene Tore"
                   })
fig_tt.update_yaxes(tick0=0, dtick=50)
left_column.plotly_chart(fig_tt, use_container_width=True)

# --- Tore pro Spiel - Teams

def get_per_team(row):
    return row["goal"]/(row["amount_games"])
teamgoals["goals_pg"] = teamgoals.apply(lambda x: get_per_team(x), axis=1)
teamgoals_sort = teamgoals.sort_values(by="goals_pg", ascending=False)
fig_tt2 = px.bar(teamgoals_sort, x="team", y="goals_pg",
                   title="Tore pro Spiel",
                   labels={
                       "team":"Mannschaft",
                       "goals_pg":"Tore pro Spiel"
                   })
fig_tt2.update_yaxes(tick0=0, dtick=10)
right_column.plotly_chart(fig_tt2, use_container_width=True)

# --- 2min pro Team ---

team_2min = df_report.groupby(["team"]).sum().sort_values(by="2min", ascending=False)
team_2min = team_2min.reset_index()

fig_t2 = px.bar(team_2min, x="team", y="2min",
                   title="2-min pro Team",
                   labels={
                       "team":"Mannschaft",
                       "2min":"Zeitstrafen"
                   })
fig_t2.update_yaxes(tick0=0, dtick=5)
left_column.plotly_chart(fig_t2, use_container_width=True)

# --- Prozent in Unterzahl ---

team_2min["Zeit2min"] = team_2min["2min"].apply(lambda x: x*2)
team_2min = pd.merge(team_2min, amount_games, on="team", how="inner")

def get_per(row):
    return (row["Zeit2min"]/(row["amount_games"]*60))*100
team_2min["percent_2min"] = team_2min.apply(lambda x: get_per(x), axis=1)
team_2min_sort = team_2min.sort_values(by="percent_2min", ascending=False)
fig_t22 = px.bar(team_2min_sort, x="team", y="percent_2min",
                   title="Verbrachte Zeit in Unterzahl",
                   labels={
                       "team":"Mannschaft",
                       "percent_2min":"Zeit in Unterzahl in %"
                   })
fig_t22.update_yaxes(tick0=0, dtick=10)
right_column.plotly_chart(fig_t22, use_container_width=True)

# --- Geworfene Tore ---

player_goals = df_report.groupby("player").sum().sort_values(by="goal", ascending=False)
player_goals.reset_index(inplace=True)
top_goals = player_goals.head(10)
top_goals_players = top_goals["player"].values.tolist()

fig_score = px.bar(top_goals, x="player", y="goal",
                   title="Top Scorer der Saison",
                   labels={
                       "player":"Spieler",
                       "goal":"Geworfene Tore"
                   })
fig_score.update_yaxes(tick0=0, dtick=5)
left_column.plotly_chart(fig_score, use_container_width=True)

# --- Tore pro Spiel - Spieler
# ### PRÜFEN, OB SPIELER GESPIELT HAT IN BERICHT ###

tps = df_report.groupby(["player", "team"]).any()
tps.reset_index(inplace=True)
tps = pd.merge(player_goals, tps[["player", "team"]], on="player", how="inner")
tps = pd.merge(tps, amount_games[["team", "amount_games"]], on="team", how="inner")
tps.sort_values(by="goal", ascending=False, inplace=True)

def goals_per_game(row):
    return row["goal"]/row["amount_games"]
tps["goals_per_game"] = tps.apply(lambda x: goals_per_game(x), axis=1)
tps.sort_values(by="goals_per_game", inplace=True, ascending=False)
tps_top = tps.head(10)

fig_gpp = px.bar(tps_top, x="player", y="goals_per_game",
                   title="Tore pro Spiel",
                   labels={
                       "player":"Spieler",
                       "goals_per_game":"Tore pro Spiel"
                   })
fig_gpp.update_yaxes(tick0=0, dtick=2)
right_column.plotly_chart(fig_gpp, use_container_width=True)


# --- Geworfene Tore in der Saison ---

time_sorted_df = df_report.sort_values(by=["game_date", "game_nr"], ascending=True)
time_sorted_df["sum_goals"] = time_sorted_df.groupby("player")["goal"].transform(pd.Series.cumsum)
date_index = time_sorted_df.groupby(["game_date", "player"]).max()
date_index = date_index.reset_index()
top_date_index = date_index[date_index["player"].isin(top_goals_players)]
fig_px = px.line(top_date_index, x="game_date",
                 y="sum_goals", color="player",
                 markers=True,
                 title="Tore im Saisonverlauf",
                    labels={
                        "game_date":"Datum",
                        "sum_goals":"Anzahl Tore"
                    })
fig_px.update_yaxes(tick0=0, dtick=5)
fig_px.update_layout(legend_title_text='Spieler')
st.plotly_chart(fig_px, use_container_width=True)

# Player Selection
st.subheader("Vergleiche den Torverlauf von zwei Spielern:")
option_player1 = st.selectbox(
    'Spieler 1:',
     all_players)
option_player2 = st.selectbox(
    'Spieler 2:',
     all_players)

option_players = [option_player1, option_player2]

selection = date_index[date_index["player"].isin(option_players)]

fig_pc = px.line(selection, x="game_date",
                 y="sum_goals", color="player",
                 markers=True,
                 title="Tore im Saisonverlauf",
                    labels={
                        "game_date":"Datum",
                        "sum_goals":"Anzahl Tore"
                    })
fig_pc.update_yaxes(tick0=0, dtick=5)
fig_pc.update_layout(legend_title_text='Spieler')
st.plotly_chart(fig_pc, use_container_width=True)




# --- Ende der Website ---
st.caption(
    " Vielen Dank für den Besuch!"
)


imp = st.checkbox("Impressum")
if imp:
    st.write(
        """
**Impressum**
Angaben gemäß § 5 TMG

Max Muster
Musterweg
12345 Musterstadt

Vertreten durch:
Max Muster

Kontakt:
Telefon: 01234-789456
Fax: 1234-56789
E-Mail: max@muster.de

Umsatzsteuer-ID:
Umsatzsteuer-Identifikationsnummer gemäß §27a Umsatzsteuergesetz: Musterustid.

Wirtschafts-ID:
Musterwirtschaftsid

Aufsichtsbehörde:
Musteraufsicht Musterstadt

Haftungsausschluss:

Haftung für Inhalte

Die Inhalte unserer Seiten wurden mit größter Sorgfalt erstellt. Für die Richtigkeit, Vollständigkeit und Aktualität der Inhalte können wir jedoch keine Gewähr übernehmen. Als Diensteanbieter sind wir gemäß § 7 Abs.1 TMG für eigene Inhalte auf diesen Seiten nach den allgemeinen Gesetzen verantwortlich. Nach §§ 8 bis 10 TMG sind wir als Diensteanbieter jedoch nicht verpflichtet, übermittelte oder gespeicherte fremde Informationen zu überwachen oder nach Umständen zu forschen, die auf eine rechtswidrige Tätigkeit hinweisen. Verpflichtungen zur Entfernung oder Sperrung der Nutzung von Informationen nach den allgemeinen Gesetzen bleiben hiervon unberührt. Eine diesbezügliche Haftung ist jedoch erst ab dem Zeitpunkt der Kenntnis einer konkreten Rechtsverletzung möglich. Bei Bekanntwerden von entsprechenden Rechtsverletzungen werden wir diese Inhalte umgehend entfernen.

Urheberrecht

Die durch die Seitenbetreiber erstellten Inhalte und Werke auf diesen Seiten unterliegen dem deutschen Urheberrecht. Die Vervielfältigung, Bearbeitung, Verbreitung und jede Art der Verwertung außerhalb der Grenzen des Urheberrechtes bedürfen der schriftlichen Zustimmung des jeweiligen Autors bzw. Erstellers. Downloads und Kopien dieser Seite sind nur für den privaten, nicht kommerziellen Gebrauch gestattet. Soweit die Inhalte auf dieser Seite nicht vom Betreiber erstellt wurden, werden die Urheberrechte Dritter beachtet. Insbesondere werden Inhalte Dritter als solche gekennzeichnet. Sollten Sie trotzdem auf eine Urheberrechtsverletzung aufmerksam werden, bitten wir um einen entsprechenden Hinweis. Bei Bekanntwerden von Rechtsverletzungen werden wir derartige Inhalte umgehend entfernen.

Datenschutz

Die Nutzung unserer Webseite ist in der Regel ohne Angabe personenbezogener Daten möglich. Soweit auf unseren Seiten personenbezogene Daten (beispielsweise Name, Anschrift oder eMail-Adressen) erhoben werden, erfolgt dies, soweit möglich, stets auf freiwilliger Basis. Diese Daten werden ohne Ihre ausdrückliche Zustimmung nicht an Dritte weitergegeben.
Wir weisen darauf hin, dass die Datenübertragung im Internet (z.B. bei der Kommunikation per E-Mail) Sicherheitslücken aufweisen kann. Ein lückenloser Schutz der Daten vor dem Zugriff durch Dritte ist nicht möglich.
Der Nutzung von im Rahmen der Impressumspflicht veröffentlichten Kontaktdaten durch Dritte zur Übersendung von nicht ausdrücklich angeforderter Werbung und Informationsmaterialien wird hiermit ausdrücklich widersprochen. Die Betreiber der Seiten behalten sich ausdrücklich rechtliche Schritte im Falle der unverlangten Zusendung von Werbeinformationen, etwa durch Spam-Mails, vor.


Google AdSense

Diese Website benutzt Google Adsense, einen Webanzeigendienst der Google Inc., USA (''Google''). Google Adsense verwendet sog. ''Cookies'' (Textdateien), die auf Ihrem Computer gespeichert werden und die eine Analyse der Benutzung der Website durch Sie ermöglicht. Google Adsense verwendet auch sog. ''Web Beacons'' (kleine unsichtbare Grafiken) zur Sammlung von Informationen. Durch die Verwendung des Web Beacons können einfache Aktionen wie der Besucherverkehr auf der Webseite aufgezeichnet und gesammelt werden. Die durch den Cookie und/oder Web Beacon erzeugten Informationen über Ihre Benutzung dieser Website (einschließlich Ihrer IP-Adresse) werden an einen Server von Google in den USA übertragen und dort gespeichert. Google wird diese Informationen benutzen, um Ihre Nutzung der Website im Hinblick auf die Anzeigen auszuwerten, um Reports über die Websiteaktivitäten und Anzeigen für die Websitebetreiber zusammenzustellen und um weitere mit der Websitenutzung und der Internetnutzung verbundene Dienstleistungen zu erbringen. Auch wird Google diese Informationen gegebenenfalls an Dritte übertragen, sofern dies gesetzlich vorgeschrieben oder soweit Dritte diese Daten im Auftrag von Google verarbeiten. Google wird in keinem Fall Ihre IP-Adresse mit anderen Daten der Google in Verbindung bringen. Das Speichern von Cookies auf Ihrer Festplatte und die Anzeige von Web Beacons können Sie verhindern, indem Sie in Ihren Browser-Einstellungen ''keine Cookies akzeptieren'' wählen (Im MS Internet-Explorer unter ''Extras > Internetoptionen > Datenschutz > Einstellung''; im Firefox unter ''Extras > Einstellungen > Datenschutz > Cookies''); wir weisen Sie jedoch darauf hin, dass Sie in diesem Fall gegebenenfalls nicht sämtliche Funktionen dieser Website voll umfänglich nutzen können. Durch die Nutzung dieser Website erklären Sie sich mit der Bearbeitung der über Sie erhobenen Daten durch Google in der zuvor beschriebenen Art und Weise und zu dem zuvor benannten Zweck einverstanden.

Impressum vom Impressum Generator der Kanzlei Hasselbach, Frankfurt


        """)







