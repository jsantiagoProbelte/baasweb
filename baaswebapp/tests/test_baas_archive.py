from django.test import TestCase
from baaswebapp.baas_archive import BaaSArchive
import os


class BaaSWebAppTest(TestCase):
    def test_baas_archive(self):
        archive = BaaSArchive(root_path='./baaswebapp/tests/fixtures/',
                              trialsFolder='./')
        self.assertTrue(
            os.path.exists('./baaswebapp/tests/fixtures/input/dummy.txt'))
        archive.createFolder('output')
        self.assertTrue(os.path.exists('./baaswebapp/tests/fixtures/output'))
        archive.uploadFile('dummy.txt',
                           './baaswebapp/tests/fixtures/input',
                           'output')
        self.assertTrue(
            os.path.exists('./baaswebapp/tests/fixtures/output/dummy.txt'))
        archive.downloadFile('dummy.txt',
                             'output/',
                             './baaswebapp/tests/fixtures/')
        self.assertTrue(
            os.path.exists('./baaswebapp/tests/fixtures/dummy.txt'))
        os.remove('./baaswebapp/tests/fixtures/output/dummy.txt')
        os.remove('./baaswebapp/tests/fixtures/dummy.txt')
        os.rmdir('./baaswebapp/tests/fixtures/output')
