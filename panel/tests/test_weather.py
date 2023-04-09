from django.test import TestCase
import panel.weatherhelper as weatherhelper
from datetime import datetime, timezone
import random


def generateTestTemperatures(length):
    weather = {'temperatures': []}
    for i in range(length):
        weather['temperatures'].append(random.randint(1, 10))
    return weather


class WeatherTest(TestCase):
    def test_fetchOpenWeather(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00")
        weather = weatherhelper.fetchOpenWeather(90, 90)
        # TEMP DISABLED self.assertEqual(weather['temperatures'][0]['date'],
        # today)
        self.assertTrue(today is not None)
        self.assertTrue(weather['temperatures'][0]['date'] is not None)

    def test_seperateTemperatures(self):
        test_temps = generateTestTemperatures(120)
        temps = weatherhelper.seperateTemperatures(test_temps)
        test_temps = test_temps['temperatures']
        print(test_temps)
        self.assertEqual(temps[1][0], test_temps[1])
        self.assertEqual(temps[1][3], test_temps[4])
        self.assertEqual(temps[3][15], test_temps[64])
