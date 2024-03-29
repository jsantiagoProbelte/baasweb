import panel.riskcalc as riskcalc
from django.test import TestCase
import random
from panel.weatherhelper import WT_TAG_TEMPS, WT_DEW_TEMP, WT_HUMIDITY


def generateRandomArray(length):
    array = []
    for i in range(length):
        array.append(random.randint(1, 20))
    return array


def generateArray(length, multiplier=1):
    array = []
    for i in range(length):
        array.append(i)
    return array


def generateTempArray(length, multiplier=1):
    array = []
    for i in range(length):
        array.append(i * multiplier)
    return array


def generateTestTemperatures():
    temperatures = []

    for i in range(5):
        temperatures.append(generateTempArray(5, (i + 1) * 5))
    return temperatures


def generateTestWeather(temperatures, WT_DEW_TEMPeratures, humidities):
    weather = {WT_TAG_TEMPS: [], WT_DEW_TEMP: [], WT_HUMIDITY: []}
    for i in range(len(temperatures)):
        weather[WT_TAG_TEMPS].append(temperatures[i])
        weather[WT_DEW_TEMP].append(WT_DEW_TEMPeratures[i])
        if humidities is not None:
            weather[WT_HUMIDITY].append(humidities[i])

    return weather


class RiskcalcTest(TestCase):
    def test_lwd(self):
        expected_lwd = [24, 24, 24, 24, 24]
        temp_array = generateRandomArray(120)
        weather = generateTestWeather(temp_array, temp_array, None)
        lwd = riskcalc.calculateLWD(weather)
        self.assertEqual(lwd, expected_lwd)

    def test_format(self):
        expected_results = ["High", "Low", "Medium", "Low", "Medium"]
        pest_input = [11, 1, 5, 1, 5]
        botrytis_input = [0.9, 0.1, 0.5, 0.2, 0.5]
        formatted_pests = []
        formatted_botrytis = []

        for i in range(5):
            formatted_pests.append(riskcalc.formatPestRisk(pest_input[i]))
            formatted_botrytis.append(
                riskcalc.formatBotrytisRisk(botrytis_input[i]))

        self.assertEqual(formatted_pests, expected_results)
        self.assertEqual(formatted_botrytis, expected_results)

    def test_botrytis(self):
        expected_results = ["Medium", "High", "High", "High", "High"]
        temperatures = generateTestWeather(
            [1, 5, 10, 15, 20], [3, 10, 2, 1, 10], None)[WT_TAG_TEMPS]
        lwd_weather = generateTestWeather(
            generateArray(120), generateArray(120), None)
        lwd = riskcalc.calculateLWD(lwd_weather)
        results = riskcalc.computeBotrytis(temperatures, lwd)
        self.assertEqual(results, expected_results)

    def test_pests(self):
        expected_results = ["Low", "Medium", "High", "High", "High"]
        temperatures = generateTestTemperatures()
        results = riskcalc.computePests(temperatures)
        self.assertEqual(results, expected_results)

    def test_all(self):
        expected_results = {
            riskcalc.RISK_BOTRITIS: ["High", "High", "High", "High", "High"],
            'pests': ["Low", "Low", "High", "High", "High"]
        }
        weather = generateTestWeather(
            generateArray(120),
            generateArray(120, 0.70),
            generateArray(120, 1.25)
        )
        results = riskcalc.computeRisks(weather)
        # print(results)
        self.assertEqual(results, expected_results)
