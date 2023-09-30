from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.contrib import auth
from baaswebapp.tests.tests_helpers import ApiRequestHelperTest
import json


class BaaSWebAppTest(TestCase):

    _apiFactory = None

    def setUp(self):
        self._apiFactory = ApiRequestHelperTest()

    def test_baaswebapp_index(self):
        response = self.client.get(reverse('baaswebapp_index'))
        # During testing, DEBUG is False
        self.assertFalse(settings.DEBUG)
        self.assertContains(response, 'BaaS in mode DEBUG= False')

    def test_login(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'Please login for full access')

    def test_user_can_login_and_logout(self):
        self.client.post(
            reverse('login'), {
                'username': ApiRequestHelperTest.USER,
                'password': ApiRequestHelperTest.PASSWORD})
        user = auth.get_user(self.client)
        self.assertEqual(user.get_username(), ApiRequestHelperTest.USER)
        self.assertTrue(user.is_authenticated)
        self.client.post(reverse('logout'))
        againUser = auth.get_user(self.client)
        self.assertFalse(againUser.is_authenticated)

    def test_wrong_user_can_login(self):
        self.client.post(
            reverse('login'), {
                'username': "badass",
                'password': ApiRequestHelperTest.PASSWORD})
        user = auth.get_user(self.client)
        self.assertNotEqual(user.get_username(), ApiRequestHelperTest.USER)

        self.client.post(
            reverse('login'), {
                'username': ApiRequestHelperTest.USER,
                'password': 'badpassword'})
        self.assertNotEqual(user.get_username(), ApiRequestHelperTest.USER)

        self.client.post(
            reverse('login'), {
                'username': '',
                'passkeys': json.dumps({'id': 123}),
                'password': 'badpassword'})
        self.assertNotEqual(user.get_username(), ApiRequestHelperTest.USER)

    def test_hidden_home(self):
        response = self.client.get(
            reverse('hidden-home'))
        self.assertContains(response, 'Dashboard')
