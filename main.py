import os

from telegram.ext import Application, CommandHandler, MessageHandler

from sabpabot.handlers.handlers import HANDLERS

TOKEN = os.getenv('SABPA_BOT_TOKEN')
BOT_USERNAME = os.getenv('SABPA_BOT_USERNAME')


def main():
    app = Application.builder().token(TOKEN).build()

    for handler in HANDLERS:
        app.add_handler(CommandHandler(handler['command_name'], handler['handler_method']))
        print(f'command {handler["command_name"]} registered!')

    app.run_polling(poll_interval=3)


if __name__ == '__main__':
    main()
