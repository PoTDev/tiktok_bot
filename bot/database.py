import mariadb
import sys
import os
from dotenv import load_dotenv
from os.path import join, dirname


class database:

    def check_connection(self, check):
        try:
            # Подключение к существующей базе данных

            dotenv_path = join(dirname(__file__), '.env')
            load_dotenv(dotenv_path)

            self.connection = mariadb.connect(user=os.environ.get("user"),
                                              password=os.environ.get("password"),
                                              host=os.environ.get("host"),
                                              port=os.environ.get("port"),
                                              database=os.environ.get("database"))
            # self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            # Курсор для выполнения операций с базой данных
            cursor = self.connection.cursor()
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                        id INT PRIMARY KEY AUTO_INCREMENT,
                        user_id INT,
                        chat_id INT,
                        username VARCHAR(255),
                        message_type INT,
                        last_activity timestamp,
                        video_type INT,
                        audio_type INT,
                        lang INT);
                        """)
            self.connection.commit()
            check = True


        except mariadb.Error as e:
            print(f"Error connecting to MariaDB Platform: {e}")

            self.connection.close()

            check = False

        return check

    # проверка пользователя в бд.
    # если нет - добавить, если есть - записать время последнего действия
    
    def user_identity(self, user_id, chat_id, username):

        db = database()

        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE chat_id=?", (chat_id,))
        print('ЧАТ АЙДИ:', chat_id)
        # Получить результат
        record = cursor.fetchone()
        # print("Вы подключены к - ", record, "\n")

        if record:
            cursor.execute("UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE chat_id=?", (chat_id,))
            self.connection.commit()
            print('Время пользователя обновлено')

        else:
            cursor = self.connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, chat_id, username, message_type, last_activity, video_type, audio_type, lang) VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP, IFNULL(NULL,0), IFNULL(NULL,0), IFNULL(NULL,0))",
                    (user_id, chat_id, username))
                self.connection.commit()
                print('NONE')
            except mariadb.Error as e:
                print(f"Error: {e}")

        self.connection.close()
        print('СОЕДИНЕНИЕ ЗАКРЫТО')

    def type_check(self, chat_id):

        db = database()

        cursor = self.connection.cursor()
        cursor.execute("SELECT message_type FROM users WHERE chat_id=?", (chat_id,))
        print('ЧАТ АЙДИ:', chat_id)
        # Получить результат

        record = cursor.fetchone()
        self.connection.close()
        print('СОЕДИНЕНИЕ ЗАКРЫТО')

        return record[0]

    def type_change(self, chat_id, type):
        db = database()

        cursor = self.connection.cursor()
        cursor.execute("UPDATE users SET message_type = ? WHERE chat_id=?", (type, chat_id,))
        self.connection.commit()
        print('Тип скачивания обновлен')

        self.connection.close()
        print('СОЕДИНЕНИЕ ЗАКРЫТО')

    def video_type_check(self, chat_id):
        db = database()

        cursor = self.connection.cursor()
        cursor.execute("SELECT video_type FROM users WHERE chat_id=?", (chat_id,))
        print('ВИДЕО ЧАТ АЙДИ:', chat_id)
        # Получить результат

        record = cursor.fetchone()
        self.connection.close()
        print('СОЕДИНЕНИЕ ЗАКРЫТО')
        return record[0]

    def video_type_change(self, chat_id, type):
        db = database()

        cursor = self.connection.cursor()
        cursor.execute("UPDATE users SET video_type = ? WHERE chat_id=?", (type, chat_id,))
        self.connection.commit()
        print('Тип скачивания видео обновлен')

        self.connection.close()
        print('СОЕДИНЕНИЕ ЗАКРЫТО')

    def audio_type_check(self, chat_id):
        db = database()

        cursor = self.connection.cursor()
        cursor.execute("SELECT audio_type FROM users WHERE chat_id=?", (chat_id,))
        print('АУДИО ЧАТ АЙДИ:', chat_id)
        # Получить результат

        record = cursor.fetchone()
        self.connection.close()
        print('СОЕДИНЕНИЕ ЗАКРЫТО')
        return record[0]

    def audio_type_change(self, chat_id, type):
        db = database()

        cursor = self.connection.cursor()
        cursor.execute("UPDATE users SET audio_type = ? WHERE chat_id=?", (type, chat_id,))
        self.connection.commit()
        print('Тип скачивания аудио обновлен')

        self.connection.close()
        print('СОЕДИНЕНИЕ ЗАКРЫТО')


