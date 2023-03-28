import math
import panel.weatherhelper as weatherhelper


def calculateLWD(weather):
    threshold = 2
    count = len(weather['temperatures'])
    temperatures = weather['temperatures']
    dew_temperatures = weather['dew_temperatures']
    lwd = []
    daily_lwd = 0
    for i in range(count):
        deficit = abs(dew_temperatures[i]
                      ['value'] - temperatures[i]['value'])
        if deficit < threshold:
            daily_lwd += 1

        if (i + 1) % 24 == 0:
            lwd.append(daily_lwd)
            daily_lwd = 0

    return lwd


def formatBotrytisRisk(risk):
    if risk > 0.8:
        return "High"
    if risk > 0.4:
        return "Medium"
    return "Low"


def formatPestRisk(gda):
    if gda > 10:
        return "High"
    if gda > 3:
        return "Medium"
    return "Low"


def computeBotrytis(temperatures, lwd):
    count = len(temperatures)
    risks = []
    for i in range(count):
        temp = temperatures[i]['value']

        risk = -4.268 - (0.0901 *
                         lwd[i]) + (0.294 * lwd[i] * temp) - \
            ((2.35 * lwd[i] * (temp ** 3)) / 100000)
        final_risk = math.exp(risk) / (1 + math.exp(risk))
        risks.append(formatBotrytisRisk(final_risk))
    return risks


def computePests(temperatures):
    base_temp = 13
    risks = []
    for day in temperatures:
        max_temp = 0
        min_temp = day[0]['value']
        for temperature in day:
            if temperature['value'] > max_temp:
                max_temp = temperature['value']
            if temperature['value'] < min_temp:
                min_temp = temperature['value']
        gda = max(0, ((min_temp + max_temp / 2) - base_temp))
        risks.append(formatPestRisk(gda))
    return risks


def computeRisks(weather):
    lwd = calculateLWD(weather)
    daily_weather = weatherhelper.formatDaily(weather)
    daily_temperatures = daily_weather['temperatures']
    seperate_temperatures = weatherhelper.seperateTemperatures(weather)

    botrytis_risks = computeBotrytis(daily_temperatures, lwd)
    pest_risks = computePests(seperate_temperatures)

    return {
        'botrytis': botrytis_risks,
        'pests': pest_risks
    }
