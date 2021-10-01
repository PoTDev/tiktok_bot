#!/usr/bin/python3.9

import os
import shutil
import click


@click.group()
def cli_start():
    pass


@cli_start.command()
def start():
    # создание нового сервиса
    shutil.copy("/usr/local/bin/ttbot/ttbot.service",
                "/etc/systemd/system/ttbot.service")

    # включение сервиса
    os.system('systemctl daemon-reload')
    os.system('systemctl enable ttbot')
    os.system('systemctl start ttbot')

    click.echo('Бот ВКЛючен')


@click.group()
def cli_stop():
    pass


@cli_stop.command()
def stop():
    # выключение
    os.system('systemctl disable ttbot')
    os.system('systemctl stop ttbot')

    click.echo('Бот ВЫКЛючен')


@click.group()
def cli_status():
    pass


@cli_status.command()
def status():
    os.system('systemctl status ttbot')


@click.group()
def cli_info():
    pass


@cli_info.command()
def info():
    click.echo('Скрипт работает')


test = click.CommandCollection(sources=[cli_start, cli_stop, cli_status, cli_info])

if __name__ == '__main__':
    test()
