from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from Collecting import init
import pandas as pd
from keras.models import load_model
import datetime
import numpy as np
import requests
from bs4 import BeautifulSoup
# startup
app = FastAPI()
SECRETE_KEY = "This is the secret key"
model = load_model("./model/Bidirect-LSTM_24h_2feature.h5")
start = datetime.datetime.now() + datetime.timedelta(hours=1)
df = init()
scheduler = BackgroundScheduler()

def hourly_task(dframe):
    env_data = []
    session = requests.Session()
    session.post('https://rapido.npnlab.com/vi/Account/Login?username=nhan&password=nhan')
    station_id = [1,2,6,10]
    current_datetime = datetime.datetime.now()
    timestamp = int(current_datetime.timestamp()*1000)
    for i in station_id:
        response = session.get('https://rapido.npnlab.com/vi/Value/GridSearch?rows=500&stationid='+str(i)+'&_='+str(timestamp))
        soup = BeautifulSoup(response.text, 'html.parser') 
        data = soup.find_all('td')
        row = []
        for i in data:
            if i.get_text()==' Sửa  Xóa':
                if len(row)==12:
                    for i in range(2,len(row),1):
                        row[i] = row[i].replace(",",".")
                    env_data.append(row[:-1])
                row=[]
            else: row.append(i.get_text())
    newdata = pd.DataFrame(env_data)
    newdata.columns = ["Record_ID","Time","Temperature","Disolved Oxygen","Salinity","pH","Turbidity","DHT Temperature","DHT Moisture","Longitude","Latitude"]
    newdata['Time'] = pd.to_datetime(newdata['Time'],format="%d/%m/%Y %H:%M:%S", dayfirst=True)
    newdata.set_index('Time', inplace=True)
    newdata.index = pd.to_datetime(newdata.index)
    newdata.sort_index(inplace=True)
    newdata['Temperature'] = newdata["Temperature"].astype(float)
    newdata = newdata['Temperature']
    newdata = newdata[newdata>=18]
    newdata = newdata.resample('H').mean()
    newdata = newdata.dropna()
    newdata = newdata[newdata.index>pd.to_datetime(dframe.tail(1).index[0])]
    dframe = pd.concat([dframe,newdata])
scheduler.add_job(hourly_task, "interval", hours=1,start_date=start, args=(df,))
scheduler.start()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def check_authorization(token: str = Depends(oauth2_scheme)):
    if token != SECRETE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/query")
async def query(request:Request,authorization: str = Depends(check_authorization)):
    query_params = dict(request.query_params)
    query_params['from'] = pd.to_datetime(datetime.datetime.fromisoformat(query_params['from']).strftime("%d/%m/%Y %H:%M:%S"),dayfirst=True).floor("H")
    query_params['to'] = pd.to_datetime(datetime.datetime.fromisoformat(query_params['to']).strftime("%d/%m/%Y %H:%M:%S"),dayfirst=True).floor("H")
    sample = df[df.index>=query_params['from']]
    sample = sample[sample.index<=query_params['to']]
    data_forecast = []
    data_real = []
    if (sample.shape[0]!=0):
        time = sample.index
        for i in range(len(time)):
            data_real.append({
                'time': time[i].strftime('%Y-%m-%dT%H:%M:%SZ'),  # Format the datetime as a string
                'data': sample[i]
            })
        
        predict_data = df[df.index<pd.to_datetime(sample.tail(1).index[0])].tail(24)
        index_array = predict_data.index
        time_array = []
        time = predict_data.index[-1]
        month = np.zeros((24,12))
        for i in range(len(predict_data)):
            month[i,index_array[i].month-1]=1
        predict_data = np.column_stack((predict_data.to_numpy(), month)).reshape(1,24,13)
        y_hat = np.empty((1,0))
        for i in range(72):
            y_hat = np.column_stack((y_hat,np.array(model.predict(predict_data[:,i:,:])).reshape(-1,1)))
            time = time + pd.Timedelta(hours=1)
            time_array.append(time)
            months = np.zeros((1,12))
            months[0,time.month-1]=1
            data = np.copy(y_hat[0,-1]).reshape(1,1)
            data = np.column_stack((data,months)).reshape(1,1,13)
            predict_data = np.column_stack((predict_data,data))
        for i in range(72):
            data_forecast.append({
                'time': time_array[i].strftime('%Y-%m-%dT%H:%M:%SZ'),  # Format the datetime as a string
                'data': y_hat[0,i]
            })
    return {
        'real':data_real,
        'forecast':data_forecast
    }

