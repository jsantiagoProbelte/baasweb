from shareplum import Site, Office365
from shareplum.site import Version
import re


USERNAME = 'baas_admin@probelte.com'
PASSWORD = 'Baspsw.2023'
SHAREPOINT_URL = 'https://probelte.sharepoint.com'
SHAREPOINT_SITE = 'https://probelte.sharepoint.com/sites/BaaSArchive/'
SHAREPOINT_DOC = 'Documentos%20compartidos/'


class SharePoint:
    def auth(self):
        self.authcookie = Office365(SHAREPOINT_URL, username=USERNAME, password=PASSWORD).GetCookies()
        self.site = Site(SHAREPOINT_SITE, version=Version.v365, authcookie=self.authcookie)

        return self.site

    def connect_folder(self, folder_name):
        self.auth_site = self.auth()

        self.sharepoint_dir = ''.join([SHAREPOINT_DOC, folder_name])
        self.folder = self.auth_site.Folder(self.sharepoint_dir)
        return self.folder

    def download_file(self, file_name, folder_name):
        self._folder = self.connect_folder(folder_name)
        return self._folder.get_file(file_name)

    def _get_files_list(self, folder_name):
        self._folder = self.connect_folder(folder_name)
        return self._folder.files

    def download_files(self, folder_name):
        self._files_list = self._get_files_list(folder_name)
        return self._files_list


class TeamsHelper():
    older_dest = '/Users/jsantiago/Code/'

    @classmethod
    def save_file(cls, file_n, file_obj):
        file_dir_path = '/'.join([cls.folder_dest, file_n])
        with open(file_dir_path, 'wb') as f:
            f.write(file_obj)
            f.close()

    @classmethod
    def getFile(cls, file_n, folder):
        file_obj = SharePoint().download_file(file_n, folder)
        cls.save_file(file_n, file_obj)

    @classmethod
    def createFolder(cls, new_folder, parent_folder):
        new_folder_path = '/'.join([parent_folder, new_folder])
        newF = SharePoint().connect_folder(new_folder_path)
        return newF

    @classmethod
    def getFiles(cls, folder):
        files_list = SharePoint().download_files(folder)
        for file in files_list:
            cls.getFile(file['Name'], folder)

    @classmethod
    def get_files_by_pattern(cls, pattern, folder):
        files_list = SharePoint().download_files(folder)
        for file in files_list:
            if re.search(pattern, file['Name']):
                cls.getFile(file['Name'], folder)

    @classmethod
    def examplePost():
        archive = SharePoint().cre
        folder_path = "studies"
        create_result = archive.create_folder(folder_path)
        if create_result:
            print("Folder successfully created in SharePoint.")
        else:
            print("Failed to create folder in SharePoint.")
