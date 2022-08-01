from __future__ import print_function

import os.path
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload
import io
import shutil




class GoogleDrive:
    def __init__(self, token_file = "token.json",
                  credentials_file = "credentials.json",
                  scopes = ['https://www.googleapis.com/auth/drive'],
                  port = 0, creds = None):
        
        self.token_file = token_file
        self.credentials_file = credentials_file
        self.scopes = scopes  # If modifying these scopes, delete the file token.json
        self.port = port 
        self.creds = creds
        self.__authenticate__()
        
    def __authenticate__(self):
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(self.token_file):
            self.creds = Credentials.from_authorized_user_file(self.token_file, self.scopes)
        # If there are no (valid) credentials available, let the user log in.
        if not self.creds or not self.creds.valid:
            if self.creds and self.creds.expired and self.creds.refresh_token:
                self.creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.credentials_file, self.scopes)
                self.creds = flow.run_local_server(port = self.port)
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(self.creds.to_json())

    def get_information(self, query = "mimeType='video/mp4'", page_size = 1000):
      
        try:
            service = build('drive', 'v3', credentials=self.creds)

            # Call the Drive v3 API
            results = service.files().list(
                pageSize=page_size,
                q=query,
                fields="nextPageToken, files(id, name)").execute()
            items = results.get('files', [])

            if not items:
                return {'name': "",  id: None}
            return items
        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')
            return {'name': "",  id: None}
    
    def get_file(self, file_id, file_name):
        try:
            service = build('drive', 'v3', credentials=self.creds)
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print ("Download %d%%." % int(status.progress() * 100))
            
            fh.seek(0)
            with open(file_name, 'wb') as f:
                shutil.copyfileobj(fh, f, length=131072)
            return True
        
        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')
            return False
                    
    def delete_file(self, file_id):
        try:
            service = build('drive', 'v3', credentials=self.creds)
            service.files().delete(fileId=file_id).execute()
            print("Deleted...")
            return True
        except HttpError as error:
            # TODO(developer) - Handle errors from drive API.
            print(f'An error occurred: {error}')
            return False



# if __name__ == '__main__':
#     g = GoogleDrive()
#     items = g.get_information(page_size = 20)      
#     if (items["name"] != ""):
#         for item in items:
#             print(item["name"], item["id"])     
#             g.get_file(item["id"], item["name"])
#         g.delete_file(item["id"])
#     else:
#         print("No file found")