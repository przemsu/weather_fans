import pandas as pd
import requests
from data.src.utils.load_html import load_html_file
from data.src.utils.load_config import load_config


def get_stadiums_and_teams() -> pd.DataFrame:

    try:
        config = load_config()

        stadiums_and_teams_html_text = load_html_file('stadiums_teams')

        # Create stadiums list
        stadiums = [i.text.strip() for i in stadiums_and_teams_html_text.find_all("td", class_= "hauptlink")]
        # Create teams list
        teams = [j.get('title') for i in stadiums_and_teams_html_text.find_all('td', class_ = 'hauptlink') for j in i.find_all('a')]
        # Create capacity list
        capacity = [row.find('td', class_='rechts').text.strip().replace('.', '') for row in stadiums_and_teams_html_text.find_all('tr') if row.find('td', class_='rechts')]
        # Create list of cities 
        cities = [table.find_all('tr')[1].get_text(strip=True) for table in stadiums_and_teams_html_text.find_all('table', class_='inline-table') if len(table.find_all('tr')) > 1]
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

        return df.to_parquet(config['processed_files']['stadium_teams_path'])
    
    # Throw excpetion when error and could not scrape data
    except requests.exceptions.RequestException as err:
        return 'Error {}'.format(err)