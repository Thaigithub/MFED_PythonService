import requests
import threading
import datetime
from bs4 import BeautifulSoup
import pandas as pd

def init():
    current_datetime = datetime.datetime.now()
    # timestamp = int(current_datetime.timestamp()*1000)
    # session = requests.Session()
    # session.post('https://rapido.npnlab.com/vi/Account/Login?username=nhan&password=nhan')

    # station_id = [1,2,6,10]
    # env_data = []

    # def collect(stationid):
    #     station_data = []
    #     page=1
    #     response = session.get('https://rapido.npnlab.com/vi/Value/GridSearch?rows=500&stationid='+str(stationid)+'&_='+str(timestamp)+"&page="+str(page))
    #     soup = BeautifulSoup(response.text, 'html.parser') 
    #     numpage = int(soup.find_all('button')[-1].get('data-page'))
    #     for page in range(numpage, 1, -1):
    #         response = session.get('https://rapido.npnlab.com/vi/Value/GridSearch?rows=500&stationid='+str(stationid)+'&_='+str(timestamp)+"&page="+str(page))
    #         soup = BeautifulSoup(response.text, 'html.parser') 
    #         data = soup.find_all('td')
    #         row = []
    #         for i in data:
    #             if i.get_text()==' Sửa  Xóa':
    #                 if len(row)==12:
    #                     for i in range(2,len(row),1):
    #                         row[i] = row[i].replace(",",".")
    #                     station_data.append(row[:-1])
    #                 row=[]
    #             else: row.append(i.get_text())
    #         print('Station '+str(stationid)+" page: "+str(page))
    #     env_data.extend(station_data)

    # threads = []
    # for i in range(len(station_id)):
    #     threads.append(threading.Thread(target=collect,args=(station_id[i],)))

    # for i in range(len(threads)):
    #     threads[i].start()
    # for i in range(len(threads)):
    #     threads[i].join()
    # df = pd.DataFrame(env_data)
    # df.to_csv('./data/'+current_datetime.strftime("%d-%m-%Y")+'.csv', index=False, header=False)
    
    # Load csv
    filename = './data/02-10-2023.csv'
    df = pd.read_csv(filename, header=None)
    
    
    df.columns = ["Record_ID","Time","Temperature","Disolved Oxygen","Salinity","pH","Turbidity","DHT Temperature","DHT Moisture","Longitude","Latitude"]
    df['Time'] = pd.to_datetime(df['Time'],format="%d/%m/%Y %H:%M:%S")
    df.set_index('Time', inplace=True)
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    df['Temperature'] = df["Temperature"].astype(float)
    df = df['Temperature']
    df = df[df>=18]
    current_datetime = current_datetime.replace(hour=current_datetime.hour, minute=0, second=0, microsecond=0)
    df = df[df.index<pd.to_datetime(current_datetime)]
    df = df.resample('H').mean()
    df = df.dropna()
    return df