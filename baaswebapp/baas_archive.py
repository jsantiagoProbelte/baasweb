from shareplum import Site, Office365
from shareplum.site import Version
import re
from django.conf import settings
import os
import shutil


class SharePoint:
    USERNAME = 'baas_admin@probelte.com'  # os.environ.get('USUARIO')
    PASSWORD = 'Baspsw.2023'  # os.environ.get('CLAVE')
    SHAREPOINT_URL = 'https://probelte.sharepoint.com'
    SHAREPOINT_SITE = 'https://probelte.sharepoint.com/sites/BaaSArchive/'
    ROOT_PATH = 'Documentos%20compartidos/'
    _root_path = None

    def __init__(self, root_path=None):
        self._root_path = self.ROOT_PATH if root_path is None\
                                         else root_path
        self.authcookie = Office365(
            SharePoint.SHAREPOINT_URL, username=SharePoint.USERNAME,
            password=SharePoint.PASSWORD).GetCookies()
        self.auth_site = Site(SharePoint.SHAREPOINT_SITE, version=Version.v365,
                              authcookie=self.authcookie)

    def connectFolder(self, folder_name):
        self.sharepoint_dir = ''.join([self._root_path, folder_name])
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
    ROOT_PATH = './../../'
    _root_path = None

    def __init__(self, root_path=None):
        self._root_path = self.ROOT_PATH if root_path is None\
                                         else root_path

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
        folder = ''.join([self._root_path, folder_name])
        self.makeFolder(folder)

    def downloadFile(self, file_name, folder_name, dest_folder):
        """
        Copy a file from the source path to the destination path.
        """
        try:
            source = ''.join([self._root_path,
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
                [self._root_path, dest_folder])
            self.connectFolder(dest_folder)
            shutil.copy2(source, destination)
            print(f"File copied from {source} to {destination}")
        except FileNotFoundError:
            print(f"Source file {source} not found")
        except shutil.SameFileError:
            print("Source and destination files are the same")


class BaaSArchive():
    DEFAULT_PATH = 'trials/'
    _trialsFolder = None
    _archive = None

    def __init__(self, root_path=None,
                 trialsFolder=None):
        if settings.TRIALS_ARCHIVE == 'TEAMS':
            self._archive = SharePoint(root_path)
        else:
            self._archive = LocalArchive(root_path)
        self._trialsFolder = trialsFolder if trialsFolder else\
            BaaSArchive.DEFAULT_PATH

    def addRoot(self, folder_name):
        return ''.join([self._trialsFolder, folder_name])

    def downloadFile(self, file_name, folder_name, dest_folder):
        self._archive.downloadFile(file_name,
                                   self.addRoot(folder_name),
                                   dest_folder)

    def createFolder(self, folder_name):
        self._archive.connectFolder(self.addRoot(folder_name))

    def uploadFile(self, file_name, folder_name, dest_folder):
        self._archive.uploadFile(file_name, folder_name,
                                 self.addRoot(dest_folder))
