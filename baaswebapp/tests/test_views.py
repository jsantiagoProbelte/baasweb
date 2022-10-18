from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import User


class BaaSWebAppTest(TestCase):

    PASSWORD = 'BaaSisAwesome'
    USER = 'pepe'

    @classmethod
    def setUpTestData(cls):
        User.objects.create_user(
            BaaSWebAppTest.USER,
            'pepe@probelte.com',
            BaaSWebAppTest.PASSWORD)

    def test_baaswebapp_index(self):
        response = self.client.get(reverse('baaswebapp_index'))
        # During testing, DEBUG is False
        self.assertFalse(settings.DEBUG)
        self.assertContains(response, 'BaaS in mode DEBUG= False')

    def test_login(self):
        response = self.client.get(reverse('login'))
        self.assertContains(response, 'Baas Web App the Agro Recommendation')

    def test_user_can_login_and_logout(self):
        self.client.post(
            reverse('login'), {
                'username': BaaSWebAppTest.USER,
                'password': BaaSWebAppTest.PASSWORD})
        user = auth.get_user(self.client)
        self.assertEqual(user.get_username(), BaaSWebAppTest.USER)
        self.assertTrue(user.is_authenticated)
        self.client.post(reverse('logout'))
        againUser = auth.get_user(self.client)
        self.assertFalse(againUser.is_authenticated)

    def test_wrong_user_can_login(self):
        self.client.post(
            reverse('login'), {
                'username': "badass",
                'password': BaaSWebAppTest.PASSWORD})
        user = auth.get_user(self.client)
        self.assertNotEqual(user.get_username(), BaaSWebAppTest.USER)

        self.client.post(
            reverse('login'), {
                'username': BaaSWebAppTest.USER,
                'password': 'badpassword'})
        self.assertNotEqual(user.get_username(), BaaSWebAppTest.USER)

        self.client.post(
            reverse('login'), {
                'username': '',
                'password': 'badpassword'})
        self.assertNotEqual(user.get_username(), BaaSWebAppTest.USER)

    def test_home(self):
        response = self.client.get(
            reverse('home'))
        self.assertContains(response, 'Dashboard')
