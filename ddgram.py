# import mariadb
import sys

import asyncio
import aiomysql


class database:

    @classmethod
    async def check_connection(cls, check):
        try:
            # Подключение к существующей базе данных
            cls.connection = await aiomysql.connect(user="root",
                                                    password="",
                                                    host="localhost",
                                                    port=3306,
                                                    db="bottiktok")
            # self.connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

            # Курсор для выполнения операций с базой данных
            cursor = await cls.connection.cursor()
            await cursor.execute("""
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
            await cls.connection.commit()
            check = True


        except Exception as e:
            print(f"Error connecting to MariaDB Platform: {e}")

            cls.connection.close()

            check = False

        return check

    # проверка пользователя в бд.
    # если нет - добавить, если есть - записать время последнего действия
    @classmethod
    async def user_identity(cls, user_id, chat_id, username):

        db = database()

        cursor = await cls.connection.cursor()
        await cursor.execute("SELECT * FROM users WHERE chat_id=%s", (chat_id,))
        print('ЧАТ АЙДИ:', chat_id)
        # Получить результат
        record = await cursor.fetchone()
        # print("Вы подключены к - ", record, "\n")

        if record:
            await cursor.execute("UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE chat_id=%s", (chat_id,))
            await cls.connection.commit()
            print('Время пользователя обновлено')

        else:
            cursor = await cls.connection.cursor()
            try:
                cursor.execute(
                    "INSERT INTO users (user_id, chat_id, username, message_type, last_activity, video_type, audio_type, lang) VALUES (%s, %s, %s, 1, CURRENT_TIMESTAMP, IFNULL(NULL,0), IFNULL(NULL,0), IFNULL(NULL,0))",
                    (user_id, chat_id, username))
                cls.connection.commit()
                print('NONE')
            except Exception as e:
                print(f"Error: {e}")

        cls.connection.close()
        print('СОЕДИНЕНИЕ ЗАКРЫТО')

    # @classmethod
    # async def type_check(cls, chat_id):
    #
    #     db = database()
    #
    #     cursor = self.connection.cursor()
    #     cursor.execute("SELECT message_type FROM users WHERE chat_id=?", (chat_id,))
    #     print('ЧАТ АЙДИ:', chat_id)
    #     # Получить результат
    #
    #     record = cursor.fetchone()
    #     self.connection.close()
    #     print('СОЕДИНЕНИЕ ЗАКРЫТО')
    #
    #     return record[0]
    #
    # @classmethod
    # async def type_change(cls, chat_id, type):
    #     db = database()
    #
    #     cursor = self.connection.cursor()
    #     cursor.execute("UPDATE users SET message_type = ? WHERE chat_id=?", (type, chat_id,))
    #     self.connection.commit()
    #     print('Тип скачивания обновлен')
    #
    #     self.connection.close()
    #     print('СОЕДИНЕНИЕ ЗАКРЫТО')
    #
    # @classmethod
    # async def video_type_check(cls, chat_id):
    #     db = database()
    #
    #     cursor = self.connection.cursor()
    #     cursor.execute("SELECT video_type FROM users WHERE chat_id=?", (chat_id,))
    #     print('ВИДЕО ЧАТ АЙДИ:', chat_id)
    #     # Получить результат
    #
    #     record = cursor.fetchone()
    #     self.connection.close()
    #     print('СОЕДИНЕНИЕ ЗАКРЫТО')
    #     return record[0]
    #
    # @classmethod
    # async def video_type_change(cls, chat_id, type):
    #     db = database()
    #
    #     cursor = self.connection.cursor()
    #     cursor.execute("UPDATE users SET video_type = ? WHERE chat_id=?", (type, chat_id,))
    #     self.connection.commit()
    #     print('Тип скачивания видео обновлен')
    #
    #     self.connection.close()
    #     print('СОЕДИНЕНИЕ ЗАКРЫТО')
    #
    # @classmethod
    # async def audio_type_check(cls, chat_id):
    #     db = database()
    #
    #     cursor = self.connection.cursor()
    #     cursor.execute("SELECT audio_type FROM users WHERE chat_id=?", (chat_id,))
    #     print('АУДИО ЧАТ АЙДИ:', chat_id)
    #     # Получить результат
    #
    #     record = cursor.fetchone()
    #     self.connection.close()
    #     print('СОЕДИНЕНИЕ ЗАКРЫТО')
    #     return record[0]
    #
    # @classmethod
    # async def audio_type_change(cls, chat_id, type):
    #     db = database()
    #
    #     cursor = self.connection.cursor()
    #     cursor.execute("UPDATE users SET audio_type = ? WHERE chat_id=?", (type, chat_id,))
    #     self.connection.commit()
    #     print('Тип скачивания аудио обновлен')
    #
    #     self.connection.close()
    #     print('СОЕДИНЕНИЕ ЗАКРЫТО')
