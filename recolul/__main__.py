import os
import requests
from bs4 import BeautifulSoup

CONTRACT_ID = os.environ["CONTRACT_ID"]
AUTH_ID = os.environ["AUTH_ID"]
PASSWORD = os.environ["PASSWORD"]


with requests.Session() as session:
    login(session)
    chart = get_attendance_chart(session)
    print(chart)
