from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from Collecting import init
import pandas as pd
from keras.models import load_model
import datetime
import numpy as np
# startup
app = FastAPI()
SECRETE_KEY = "This is the secret key"
model = load_model("./model/Bidirect-LSTM_24h_2feature.h5")
df = init()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
def check_authorization(token: str = Depends(oauth2_scheme)):
    if token != SECRETE_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/query")
async def query(request:Request,authorization: str = Depends(check_authorization)):
    query_params = dict(request.query_params)
    query_params['from'] = pd.to_datetime(datetime.datetime.fromisoformat(query_params['from']).strftime("%d/%m/%Y %H:%M:%S")).floor("H")
    query_params['to'] = pd.to_datetime(datetime.datetime.fromisoformat(query_params['to']).strftime("%d/%m/%Y %H:%M:%S")).floor("H")
    sample = df[df.index>=query_params['from']]
    sample = sample[sample.index<=query_params['to']]
    time = sample.index
    data_real = []
    for i in range(len(time)):
        data_real.append({
            'time': time[i].strftime('%Y-%m-%dT%H:%M:%SZ'),  # Format the datetime as a string
            'data': sample[i]
        })
    predict_data = sample.tail(24)
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
    data_forecast = []
    for i in range(72):
        data_forecast.append({
            'time': time_array[i].strftime('%Y-%m-%dT%H:%M:%SZ'),  # Format the datetime as a string
            'data': y_hat[0,i]
        })
    print(time_array)
    return {
        'real':data_real,
        'forecast':data_forecast
    }

