import os
import shutil

#создание нового сервиса
shutil.copy("/usr/local/bin/ttbot/ttbot.service", 
"/etc/systemd/system/ttbot.service")


#включение сервиса
os.system('systemctl daemon-reload')
os.system('systemctl enable ttbot')
os.system('systemctl start ttbot')

print('Выполнено')