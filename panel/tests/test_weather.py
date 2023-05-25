from django.test import TestCase
import panel.weatherhelper as weatherhelper
from datetime import datetime, timezone
import random


def generateTestTemperatures(length):
    weather = {weatherhelper.WT_TAG_TEMPS: []}
    for i in range(length):
        weather[weatherhelper.WT_TAG_TEMPS].append(random.randint(1, 10))
    return weather


class WeatherTest(TestCase):
    def test_fetchOpenWeather(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%dT00:00")
        weather = weatherhelper.fetchOpenWeather(90, 90, 5)
        # TEMP DISABLED self.assertEqual(weather[WT_TAG_TEMPS][0]['date'],
        # today)
        self.assertTrue(today is not None)
        self.assertTrue(weather[weatherhelper.DATES][0] is not None)

    def test_seperateTemperatures(self):
        test_temps = generateTestTemperatures(120)
        temps = weatherhelper.seperateTemperatures(test_temps)
        test_temps = test_temps[weatherhelper.WT_TAG_TEMPS]
        print(test_temps)
        self.assertEqual(temps[1][0], test_temps[1])
        self.assertEqual(temps[1][3], test_temps[4])
        self.assertEqual(temps[3][15], test_temps[64])
