import requests
import threading
import datetime
from bs4 import BeautifulSoup
import pandas as pd

def init():
    current_datetime = datetime.datetime.now()
    timestamp = int(current_datetime.timestamp()*1000)
    session = requests.Session()
    session.post('https://rapido.npnlab.com/vi/Account/Login?username=nhan&password=nhan')

    station_id = [1,2,6,10]
    env_data = []

    def collect(stationid):
        station_data = []
        page=1
        response = session.get('https://rapido.npnlab.com/vi/Value/GridSearch?rows=500&stationid='+str(stationid)+'&_='+str(timestamp)+"&_page="+str(page))
        soup = BeautifulSoup(response.text, 'html.parser') 
        numpage = int(soup.find_all('button')[-1].get('data-page'))
        for page in range(numpage, 1, -1):
            response = session.get('https://rapido.npnlab.com/vi/Value/GridSearch?rows=500&stationid='+str(stationid)+'&_='+str(timestamp)+"&_page="+str(page))
            soup = BeautifulSoup(response.text, 'html.parser') 
            data = soup.find_all('td')
            row = []
            for i in data:
                if i.get_text()==' Sửa  Xóa':
                    if len(row)==12:
                        station_data.append(row[:-1])
                    row=[]
                else: row.append(i.get_text())
        env_data.extend(station_data)

    threads = []
    for i in range(len(station_id)):
        threads.append(threading.Thread(target=collect,args=(station_id[i],)))

    for i in range(len(threads)):
        threads[i].start()
    for i in range(len(threads)):
        threads[i].join()

    df = pd.DataFrame(env_data)
    df.columns = ["Record_ID","Time","Temperature","Disolved Oxygen","Salinity","pH","Turbidity","DHT Temperature","DHT Moisture","Longitude","Latitude"]
    df.to_csv(current_datetime.strftime("%d-%m-%Y")+'.csv', index=False, header=False)
