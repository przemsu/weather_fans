import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

def get_stadiums_and_teams() -> pd.DataFrame:

    headers = {
        'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
    }
    response = requests.get(
        'https://www.transfermarkt.pl/betclic-1-liga/stadien/wettbewerb/PL2/plus/1',
        headers=headers
        )

    response_text = response.text

    soup = BeautifulSoup(response_text, 'html.parser')

    # Create stadiums list
    stadiums = [i.text.strip() for i in soup.find_all("td", class_= "hauptlink")]
    # Create teams list
    teams = [j.get('title') for i in soup.find_all('td', class_ = 'hauptlink') for j in i.find_all('a')]
    # Create capacity list
    capacity = [row.find('td', class_='rechts').text.strip().replace('.', '') for row in soup.find_all('tr') if row.find('td', class_='rechts')]
    # Create list of cities 
    cities = [table.find_all('tr')[1].get_text(strip=True) for table in soup.find_all('table', class_='inline-table') if len(table.find_all('tr')) > 1]
    # List of lists to unzip for data frame
    zipped_lists = [stadiums, teams, capacity, cities]
    # Zip stadiums and teams lists and create pandas df
    stadiums_teams = zip(*zipped_lists)
    # Create df with scraped data
    df = pd.DataFrame(stadiums_teams, columns=['stadium', 'team', 'capacity', 'city']).reset_index(drop=True)

    # Replace two cities which are written withou polish signs on the webiste + add missing city - Wieczysta Kraków is playing outside origin city
    cities_correction = {
        'Pruszkow': 'Pruszków',
        'Chorzow': 'Chorzów',
        '': 'Sosnowiec'
    }

    df['city'] = df['city'].replace(cities_correction)

    return df

def get_matches_and_attendance() -> pd.DataFrame:

    headers = {
            'user_agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36'
        }
    
    response = requests.get(
        'http://www.90minut.pl/liga/1/liga14073.html',
        headers=headers
        )
    
    response_text = response.text

    # Scrape data using pandas library
    dfs = pd.read_html(
        response_text,
        encoding = 'utf-8',
        attrs = {'class': 'main'},
        flavor ='lxml'
    )

    # Join all df from the list after scraping
    df = pd.concat(dfs)
    # Rename default colum names
    df_renamed = df.rename(columns={0: "home_team", 1: "score", 2: "away_team", 3: "date"})
    # Set flag where value in 'home_team' column and 'score' is the same as data is parsed with goal scorers which is not needed for analysis
    df_renamed['compare'] = df_renamed['home_team'].str.strip().str.lower() == df_renamed['score'].str.strip().str.lower()
    # Create new df with only relevant rows
    df_new = df_renamed.loc[df_renamed['compare'] == False].copy()
    df_new[['home_score', 'away_score']] = df_new['score'].str.extract(r'(\d+)-(\d+)')
    df_new['day_date'] = df_new['date'].str.extract(r'(\d+\s+\w+)', expand=False)
    df_new['match_hour'] = df_new['date'].str.extract(r'(\d+:\d+)', expand=False)
    df_new['match_attendance'] = df_new['date'].str.extract(r'\(([^)]*)\)')[0].replace(r'\s+', '', regex=True)

    day_unique = list(df_new['day_date'].str.replace(r'\d+\s+', '', regex=True).unique())
    proper_month = ['07.2025', '08.2025', '10.2025', '09.2025', '11.2025', '12.2025', '02.2026', '03.2026', '04.2026', '05.2026']

    day_dict = dict(zip(day_unique, proper_month))
    # Fill data when length of day is 1 with 0 eg. 4.07.2025 -> 04.07.2025
    df_new['match_day_date'] = df_new['day_date'].str.extract(r'(\d+)', expand=False).str.zfill(2) + '.' + df_new['day_date'].str.replace(r'\d+\s+', '', regex=True).map(day_dict)
    
    # Drop na values and unecessary columns
    df_dropna = df_new.dropna()
    df_attendance = df_dropna.drop(['score', 'date', 'day_date', 'compare'], axis=1)

    return df_attendance

def join_dfs() -> pd.DataFrame:

    stadiums_teams = get_stadiums_and_teams()
    matches_attendace = get_matches_and_attendance()

    df = matches_attendace.set_index("home_team").join(stadiums_teams.set_index("team"))

    return df

if __name__ == '__main__':
    join_dfs()