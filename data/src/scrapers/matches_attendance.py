import requests
from data.src.utils.load_config import load_config

def get_matches_and_attendance():

    config = load_config()

    headers = {
        config['scraping_headers']['user']: config['scraping_headers']['browser']
    }

    try:
        response = requests.get(
            config['urls']['matches_attendance'],
            headers=headers
            )

        with open(config['raw_files']['matches_attendance_path'], "w", encoding="utf-8") as f:
            f.write(response.text)
            return response.text
    
    except requests.exceptions.RequestException as err:
        return 'Error {}'.format(err)