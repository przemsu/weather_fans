import pandas as pd
import requests
from data.src.utils.load_html import load_html_file
from data.src.utils.load_config import load_config

def get_matches_and_attendance():

    try:
        config = load_config()

        matches_and_attendance_html_text = load_html_file('matches_attendance')

        # Scrape data using pandas library
        dfs = pd.read_html(
            str(matches_and_attendance_html_text),
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

        # Change date from 20 lipca to 20.07.2025
        day_unique = list(df_new['day_date'].str.replace(r'\d+\s+', '', regex=True).unique())
        proper_month = ['07.2025', '08.2025', '10.2025', '09.2025', '11.2025', '12.2025', '02.2026', '03.2026', '04.2026', '05.2026']

        day_dict = dict(zip(day_unique, proper_month))
        # Fill data when length of day is 1 with 0 eg. 4.07.2025 -> 04.07.2025
        df_new['match_day_date'] = df_new['day_date'].str.extract(r'(\d+)', expand=False).str.zfill(2) + '.' + df_new['day_date'].str.replace(r'\d+\s+', '', regex=True).map(day_dict)
        
        # Drop na values and unecessary columns
        df_dropna = df_new.dropna()
        df_attendance = df_dropna.drop(['score', 'date', 'day_date', 'compare'], axis=1)

        return df_attendance.to_parquet(config['processed_files']['matches_attendance_path'])

    # Throw excpetion when error and could not scrape data
    except requests.exceptions.RequestException as err:
        return 'Error {}'.format(err)
    
get_matches_and_attendance()