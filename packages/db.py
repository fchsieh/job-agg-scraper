"""
Pushes data to firebase
"""

import logging
import os

import firebase_admin
from firebase_admin import credentials, firestore


class DB:
    def __init__(self):
        self.db = None
        self.logger = logging.getLogger("Database")
        self.init_db()

    def init_db(self):
        if not firebase_admin._apps:
            path = os.path.join(os.path.dirname(__file__), "firebase.json")
            cred = credentials.Certificate(path)
            firebase_admin.initialize_app(
                cred, {"databaseURL": "https://job-scraper-6454d.firebaseio.com"}
            )

        self.db = firestore.client().collection("data")
        # check if connected
        if self.db:
            self.logger.info("Connected to firebase database")
        else:
            self.logger.error("Failed to connect to firebase database")
            exit(1)

    def push(self, data):
        try:
            self.db.document("jobs").set(data)
            self.logger.info("Pushed data to database")
        except Exception as e:
            self.logger.error("Error pushing data to database: {}".format(e))
            return False
