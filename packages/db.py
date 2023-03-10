"""
Pushes data to firebase
"""

import logging
import os

import firebase_admin
from firebase_admin import credentials, firestore


class DB:
    def __init__(self, config):
        self.db = None
        self.config = config
        self.logger = logging.getLogger("Database")
        self.init_db()

    def init_db(self):
        if not firebase_admin._apps:
            path = os.path.join("..", self.config["firebase"]["credentials"])
            # check if file exists
            if not os.path.exists(path):
                self.logger.error("Firebase {} config file not found".format(path))
                exit(1)
            cred = credentials.Certificate(path)
            firebase_admin.initialize_app(
                cred, {"databaseURL": self.config["firebase"]["url"]}
            )

        self.db = firestore.client().collection(self.config["database"]["collection"])
        # check if connected
        if self.db:
            self.logger.info("Connected to firebase database")
        else:
            self.logger.error("Failed to connect to firebase database")
            exit(1)

    def push(self, data):
        for key, value in data.items():
            try:
                self.db.document(key).set({self.config["database"]["document"]: value})
            except Exception as e:
                self.logger.error("Error pushing data to database: {}".format(e))
                return False
            finally:
                self.logger.info(
                    "Pushed {} jobs to database for {}".format(len(value), key)
                )
