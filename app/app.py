import pandas as pd
import streamlit as st
import altair as alt
import seaborn as sns
import plotly.express as px
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# --- Setup Streamlit ---
st.set_page_config(layout="wide")

#df_report = pd.read_csv(r"C:\Users\rgrie\PycharmProjects\handball-stats\data\220316_mHSOL_ab.csv", parse_dates=[3], dayfirst=True)

df_report = pd.read_csv(r"https://raw.githubusercontent.com/therealgriehl/handball-stats/main/data/220316_mHSOL_ab.csv")

all_games = df_report["game_nr"].unique().tolist()
all_teams = np.unique(df_report[["home", "guest", "team"]].values)
all_players = df_report["player"].unique().tolist()

st.title("Hello World")

st.header("DataFrame")
st.dataframe(df_report)

left_column, right_column = st.columns(2)

left_column.header("Tore pro Team")
teamgoals = df_report.groupby(["team"]).sum().sort_values(by="goal", ascending=False)
left_column.bar_chart(teamgoals["goal"])

right_column.header("2min pro Team")
team_2min = df_report.groupby(["team"]).sum().sort_values(by="2min", ascending=False)
right_column.bar_chart(team_2min["2min"])

# --- Geworfene Tore ---
st.header("Top Scorer")
player_goals = df_report.groupby("player").sum().sort_values(by="goal", ascending=False)
top_goals = player_goals.head(10)
top_goals_players = top_goals.index.values.tolist()
st.bar_chart(top_goals["goal"])

# --- Geworfene Tore in der Saison ---

st.subheader("Top Scorer im Saisonverlauf")
time_sorted_df = df_report.sort_values(by=["game_date", "game_nr"], ascending=True)
time_sorted_df["sum_goals"] = time_sorted_df.groupby("player")["goal"].transform(pd.Series.cumsum)
date_index = time_sorted_df.groupby(["game_date", "player"]).max()
date_index = date_index.reset_index()
top_date_index = date_index[date_index["player"].isin(top_goals_players)]

fig_px = px.line(top_date_index, x="game_date", y="sum_goals", color="player", markers=True)
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
fig = plt.figure(figsize=(15,6))
sns.lineplot(data=selection, x="game_date", y="sum_goals", hue="player", marker='o',linestyle="--")
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
plt.xlabel("Datum")
plt.ylabel("Tore")
st.pyplot(fig)


# --- Teams im Saisonverlauf ---
st.header("Teams im Saisonverlauf")
games_df = time_sorted_df.groupby(["game_nr", "team"])["goal"].sum()
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

merged_df = pd.merge(time_sorted_df, wins_df, on="game_nr", how="inner")

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

fig2 = plt.figure(figsize=(15,8))
sns.lineplot(data=points_df, x="game_date", y="sum_points+", hue="team", marker='o',linestyle="--")
plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0)
st.pyplot(fig2)





# --- Ende der Website ---

st.caption(
    " Vielen Dank für den Besuch!"
)




