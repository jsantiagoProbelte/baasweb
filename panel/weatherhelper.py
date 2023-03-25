import requests
from datetime import datetime
import json
import base64
# Secret
base64key = base64.b64encode(
    "probelte_arentz:z0GuO6Tk6l".encode("ascii")).decode("ascii")


def fetchWeather(latitude, longitude):
    headers = {'Authorization': 'Basic ' + base64key}
    res = requests.get(
        'https://api.meteomatics.com/' +
        datetime.now().strftime('%Y-%m-%dT00:00:00Z') +
        'P5D:PT1H/t_min_2m_1h:C,dew_point_2m:C,absolute_humidity_2m:gm3/' +
        str(latitude) + ','
        + str(longitude) + '/json?model=mix', headers=headers)
    res_json = json.loads(res.content)

    return formatWeather(res_json)


def fetchOpenWeather(latitude, longitude):
    res = requests.get('https://api.open-meteo.com/v1/forecast?latitude=' + str(
        latitude) + '&longitude=' + str(longitude) + '&hourly=temperature_2m,relativehumidity_2m,dewpoint_2m&forecast_days=5')
    res_json = json.loads(res.content)

    return formatOpenWeather(res_json)


def formatWeather(res_json):
    temperatures = res_json['data'][0]['coordinates'][0]['dates']
    dew_temperatures = res_json['data'][1]['coordinates'][0]['dates']
    humidities = res_json['data'][2]['coordinates'][0]['dates']

    # Meteomatics always returns 1 hour extra, so we pop it.
    temperatures.pop()
    dew_temperatures.pop()
    humidities.pop()

    return {
        'temperatures': temperatures,
        'dew_temperatures': dew_temperatures,
        'humidities': humidities
    }


def formatOpenWeather(res_json):
    temperatures = res_json['hourly']['temperature_2m']
    dew_temperatures = res_json['hourly']['dewpoint_2m']
    humidities = res_json['hourly']['relativehumidity_2m']
    dates = res_json['hourly']['time']
    count = len(temperatures)

    for i in range(count):
        temperatures[i] = {'date': dates[i], 'value': temperatures[i]}
        dew_temperatures[i] = {'date': dates[i],
                               'value': dew_temperatures[i]}
        humidities[i] = {'date': dates[i], 'value': humidities[i]}

    return {
        'temperatures': temperatures,
        'dew_temperatures': dew_temperatures,
        'humidities': humidities
    }


def formatDaily(weather):
    offset = 12
    temperatures = weather['temperatures']
    dew_temperatures = weather['dew_temperatures']
    humidities = weather['humidities']

    daily_temperatures = []
    daily_dew = []
    daily_humidity = []

    for i in range(len(temperatures)):
        if i % 24 == 0:
            daily_temperatures.append(temperatures[i + offset])
            daily_dew.append(dew_temperatures[i + offset])
            daily_humidity.append(humidities[i + offset])

    return {
        'temperatures': daily_temperatures,
        'dew_temperatures': daily_dew,
        'humidities': daily_humidity
    }


def seperateTemperatures(weather):
    temperatures = weather['temperatures']
    daily_temperatures = []
    formatted_temperatures = []

    for i in range(len(temperatures)):
        daily_temperatures.append(temperatures[i])
        if i % 24 == 0:
            formatted_temperatures.append(daily_temperatures)
            daily_temperatures = []

    return formatted_temperatures
