import requests
import json


WT_DEW_TEMP = 'Dew temperature (°C)'
WT_TAG_TEMPS = 'Temperature (°C)'
WT_HUMIDITY = 'Absolute humidity'


def fetchOpenWeather(latitude, longitude, nextDays):
    res = requests.get(
        'https://api.open-meteo.com/v1/forecast?latitude=' +
        str(latitude) + '&longitude=' + str(longitude) +
        '&hourly=temperature_2m,relativehumidity_2m,dewpoint_2m&'
        'forecast_days=' + str(nextDays))
    res_json = json.loads(res.content)

    return formatOpenWeather(res_json)


def formatOpenWeather(res_json):
    temperatures = res_json['hourly']['temperature_2m']
    WT_DEW_TEMPeratures = res_json['hourly']['dewpoint_2m']
    humidities = res_json['hourly']['relativehumidity_2m']
    dates = res_json['hourly']['time']
    count = len(temperatures)

    for i in range(count):
        temperatures[i] = {'date': dates[i], 'value': temperatures[i]}
        WT_DEW_TEMPeratures[i] = {'date': dates[i],
                                  'value': WT_DEW_TEMPeratures[i]}
        humidities[i] = {'date': dates[i], 'value': humidities[i]}

    return {
        WT_TAG_TEMPS: temperatures,
        WT_DEW_TEMP: WT_DEW_TEMPeratures,
        WT_HUMIDITY: humidities
    }


def formatDaily(weather):
    offset = 12
    temperatures = weather[WT_TAG_TEMPS]
    WT_DEW_TEMPeratures = weather[WT_DEW_TEMP]
    humidities = weather[WT_HUMIDITY]

    daily_temperatures = []
    daily_dew = []
    daily_humidity = []

    for i in range(len(temperatures)):
        if i % 24 == 0:
            daily_temperatures.append(temperatures[i + offset])
            daily_dew.append(WT_DEW_TEMPeratures[i + offset])
            daily_humidity.append(humidities[i + offset])
    return {WT_TAG_TEMPS: daily_temperatures,
            WT_DEW_TEMP: daily_dew,
            WT_HUMIDITY: daily_humidity}


def seperateTemperatures(weather):
    temperatures = weather[WT_TAG_TEMPS]
    daily_temperatures = []
    formatted_temperatures = []

    for i in range(len(temperatures)):
        daily_temperatures.append(temperatures[i])
        if i % 24 == 0:
            formatted_temperatures.append(daily_temperatures)
            daily_temperatures = []

    return formatted_temperatures


"""
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
"""

"""
def formatWeather(res_json):
    temperatures = res_json['data'][0]['coordinates'][0]['dates']
    WT_DEW_TEMPeratures = res_json['data'][1]['coordinates'][0]['dates']
    humidities = res_json['data'][2]['coordinates'][0]['dates']

    # Meteomatics always returns 1 hour extra, so we pop it.
    temperatures.pop()
    WT_DEW_TEMPeratures.pop()
    humidities.pop()

    return {
        WT_TAG_TEMPS: temperatures,
        WT_DEW_TEMP: WT_DEW_TEMPeratures,
        WT_HUMIDITY: humidities
    }
"""
