import sqlite3
from config import Step


class SQLighter:

    def __init__(self, db_name):
        self.con = sqlite3.connect(db_name)
        self.cursor = self.con.cursor()

    def add_client(self, chat_id, username):
        with self.con:
            self.cursor.execute("INSERT INTO `clients` (`chat_id`, `username`, `step`) VALUES (?, ?, ?)",
                                (chat_id, username, Step.CHOOSE_WORK_TYPE.value))

    def update_work_type(self, username, work_type):
        with self.con:
            self.cursor.execute("UPDATE `clients` SET `work_type`= ? WHERE `username` == ?", (work_type, username))

    def update_budget(self, username, budget):
        with self.con:
            self.cursor.execute("UPDATE `clients` SET `budget`= ? WHERE `username` == ?", (budget, username))

    def update_task_file(self, username, task_file):
        with self.con:
            self.cursor.execute("UPDATE `clients` SET `task_file` = ? WHERE `username` == ?", (task_file, username))

    def update_step(self, username, step):
        with self.con:
            self.cursor.execute("UPDATE `clients` SET `step` = ? WHERE `username` == ?", (step, username))

    def get_step(self, username):
        with self.con:
            return self.cursor.execute("SELECT `step` FROM `clients` WHERE `username` == ?", [username]).fetchone()

    def get_client_data(self, username):
        with self.con:
            return self.cursor.execute("SELECT * FROM `clients` WHERE `username` == ?", [username]).fetchone()

    def active_order(self, username):
        with self.con:
            self.cursor.execute("UPDATE `clients` SET `status` = TRUE WHERE `username` == ?", [username])

    def get_order_status(self, username):
        with self.con:
            return self.cursor.execute("SELECT `status` FROM `clients` WHERE `username` == ?", [username]).fetchone()

    def reset_data(self, username):
        with self.con:
            self.cursor.execute("UPDATE `clients` SET `work_type` = NULL, `budget` = NULL, `task_file` = NULL, \
            `status` = 0, `step` = ? WHERE `username` == ?", (Step.CHOOSE_WORK_TYPE.value, username))
