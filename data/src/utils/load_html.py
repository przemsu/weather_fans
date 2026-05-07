from bs4 import BeautifulSoup

def load_html_file(file_name):

    with open(f'data/raw/{file_name}.html', 'r') as file:
        return BeautifulSoup(file, 'html.parser')
    
load_html_file('stadiums_teams')
