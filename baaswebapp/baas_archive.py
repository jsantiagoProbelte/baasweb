from shareplum import Site, Office365
from shareplum.site import Version
import re
from django.conf import settings
import os
import shutil


class SharePoint:
    USERNAME = 'baas_admin@probelte.com'
    PASSWORD = 'Baspsw.2023'
    SHAREPOINT_URL = 'https://probelte.sharepoint.com'
    SHAREPOINT_SITE = 'https://probelte.sharepoint.com/sites/BaaSArchive/'
    SHAREPOINT_DOC = 'Documentos%20compartidos/'

    def __init__(self):
        self.authcookie = Office365(
            SharePoint.SHAREPOINT_URL, username=SharePoint.USERNAME,
            password=SharePoint.PASSWORD).GetCookies()
        self.auth_site = Site(SharePoint.SHAREPOINT_SITE, version=Version.v365,
                              authcookie=self.authcookie)

    def connectFolder(self, folder_name):
        self.sharepoint_dir = ''.join([SharePoint.SHAREPOINT_DOC, folder_name])
        self._folder = self.auth_site.Folder(self.sharepoint_dir)

    def _download_file(self, file_name, dest_folder):
        file_obj = self._folder.get_file(file_name)
        file_dir_path = '/'.join([dest_folder, file_name])
        with open(file_dir_path, 'wb') as f:
            f.write(file_obj)
            f.close()

    def downloadFile(self, file_name, folder_name, dest_folder):
        self.connectFolder(folder_name)
        self._download_file(file_name, dest_folder)

    def uploadFile(self, file_name, folder_name, dest_folder):
        self.connectFolder(dest_folder)
        filePath = ''.join([folder_name, file_name])
        with open(filePath, mode='rb') as file:
            fileContent = file.read()
        self._folder.upload_file(fileContent, file_name)

    def _get_files_list(self):
        return self._folder.files

    def downloadFiles(self, folder_name, folder_destination,
                      pattern=None):
        self.connectFolder(folder_name)
        for file in self._get_files_list(folder_name):
            if pattern and not re.search(pattern, file['Name']):
                continue
            self._download_file(file['Name'], folder_destination)


class LocalArchive():
    LOCAL_ARCHIVE = './../../'

    def makeFolder(self, folder_name):
        try:
            os.makedirs(folder_name)
            print(f"Folder created at {folder_name}")
        except FileExistsError:
            print(f"Folder already exists at {folder_name}")

    def connectFolder(self, folder_name):
        """
        Create a new folder at the specified path.
        """
        folder = ''.join([LocalArchive.LOCAL_ARCHIVE, folder_name])
        self.makeFolder(folder)

    def downloadFile(self, file_name, folder_name, dest_folder):
        """
        Copy a file from the source path to the destination path.
        """
        try:
            source = ''.join([LocalArchive.LOCAL_ARCHIVE,
                              folder_name, file_name])
            self.makeFolder(dest_folder)
            shutil.copy2(source, dest_folder)
            print(f"File copied from {source} to {dest_folder}")
        except FileNotFoundError:
            print(f"Source file {source} not found")
        except shutil.SameFileError:
            print("Source and destination files are the same")

    def uploadFile(self, file_name, folder_name, dest_folder):
        """
        Copy a file from the source path to the destination path.
        """
        try:
            source = '/'.join([folder_name, file_name])
            destination = ''.join(
                [LocalArchive.LOCAL_ARCHIVE, dest_folder])
            self.connectFolder(dest_folder)
            shutil.copy2(source, destination)
            print(f"File copied from {source} to {destination}")
        except FileNotFoundError:
            print(f"Source file {source} not found")
        except shutil.SameFileError:
            print("Source and destination files are the same")


class BaaSArchive():
    _trialsFolder = 'trials/'
    _archive = None

    def __init__(self):
        if settings.TRIALS_ARCHIVE == 'TEAMS':
            self._archive = SharePoint()
        else:
            self._archive = LocalArchive()

    def addRoot(self, folder_name):
        return ''.join([BaaSArchive._trialsFolder, folder_name])

    def downloadFile(self, file_name, folder_name, dest_folder):
        self._archive.downloadFile(file_name,
                                   self.addRoot(folder_name),
                                   dest_folder)

    def createFolder(self, folder_name):
        self._archive.connectFolder(self.addRoot(folder_name))

    def uploadFile(self, file_name, folder_name, dest_folder):
        self._archive.uploadFile(file_name, folder_name,
                                 self.addRoot(dest_folder))
