import logging
import yaml
import sys
from sshtunnel import SSHTunnelForwarder

from telegram import __version__ as TG_VER
from telegram import BotCommand

try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]
if __version_info__ < (20, 0, 0, "alpha", 1):
    raise RuntimeError(
        f"This bot is not compatible with your current PTB version {TG_VER}. To upgrade use this command:"
        f"pip3 install python-telegram-bot --upgrade --pre"
    )
from telegram.ext import Application, CommandHandler,ContextTypes

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logging.getLogger(__name__)

VERSION = "2.0"

try:
    f = open('config.yaml', 'r')
    config = yaml.safe_load(f)
except FileNotFoundError as error:
    print(error)
    sys.exit(0)

try:
    ssh_cfg = config['v2board']['ssh']
    db_cfg = config['v2board']['database']
    port = db_cfg['port']
    if ssh_cfg['enable'] is True:
        ssh = SSHTunnelForwarder(
            ssh_address_or_host=(ssh_cfg['ip'], ssh_cfg['port']),
            ssh_username=ssh_cfg['user'],
            ssh_password=ssh_cfg['pass'],
            remote_bind_address=(db_cfg['ip'], db_cfg['port']))
        ssh.start()
        port = ssh.local_bind_port
except Exception as error:
    print(error)
    sys.exit(0)

try:
    proxy = 'http://127.0.0.1:7890'
    token = config['bot']['token']
    #app = Application.builder().token(token).build()
    app = Application.builder().token(token).proxy_url(proxy).get_updates_proxy_url(proxy).build()
except Exception as error:
    print(error)
    sys.exit(0)


async def onCommandSet(context: ContextTypes.DEFAULT_TYPE):
    await context.bot.delete_my_commands()
    await context.bot.set_my_commands(context.job.data)



def main():
    try:
        import Commands
        command_list = []
        for i in Commands.content:
            app.add_handler(CommandHandler(i, getattr(Commands, i).exec))
            command_list.append(BotCommand(i,getattr(Commands, i).desc))
        app.job_queue.run_once(onCommandSet,1,command_list,'onCommandSet')
        import Modules
        for i in Modules.content:
            app.job_queue.run_repeating(
                getattr(Modules, i).exec, interval=60, first=10, name=i)
        app.run_polling(drop_pending_updates=True)
    except Exception as error:
        print(error)
        sys.exit(0)


if __name__ == "__main__":
    main()
