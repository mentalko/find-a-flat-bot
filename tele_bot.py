from telegram.ext import Updater, CommandHandler
import signal
import pickle
import os
import sys
import logging
token = os.environ["FINDAFLATTOKEN"]


class Users:
    def __init__(self):
        self.uids = {}
        if os.path.exists('uid'):
            with open('uid', 'rb') as f:
                self.uids = pickle.load(f)
        logging.info("Loaded %s", self.uids)

    def save_uids(self):
        with open('uid', 'wb') as f:
            pickle.dump(self.uids, f)


    def __iter__(self):
        return iter(self.uids.items())

    def new_user(self, bot, update, args):
        logging.info("New user args: %s", args)
        self.uids[update.message.chat_id] = args[0]
        bot.send_message(chat_id=update.message.chat_id, text="Hello! Now you'll receive notifications." \
                                                            "Say /stop to disable")

    def delete_user(self, bot, update):
        del self.uids[update.message.chat_id]
        bot.send_message(chat_id=update.message.chat_id, text="Notifications disabled")

# os.environ['HTTPS_PROXY'] = 'socks5://127.0.0.1:52820'
# os.environ['HTTPS_PROXY'] = 'socks5://127.0.0.1:52821'
proxy = {
    'proxy_url': 'socks5://127.0.0.1:52820',
    'read_timeout': 26, 'connect_timeout': 27
}


def start_bot():
    updater = Updater(token, request_kwargs=proxy)
    users = Users()
    start_handler = CommandHandler('start', users.new_user, pass_args=True)
    delete_handler = CommandHandler('stop', users.delete_user)
    updater.dispatcher.add_handler(start_handler)
    updater.dispatcher.add_handler(delete_handler)
    updater.start_polling()

    def sender(uid, msg):
        if msg.startswith('http'):
            print(msg)
            updater.bot.send_photo(uid, msg, timeout=20)
        else:
            updater.bot.send_message(uid, msg, timeout=20)


    def signal_handler(sig, frame, stop, users):
        logging.info("Ctrl+C pressed, processing...")
        users.save_uids()
        logging.info("uids saved")
        stop()
        logging.info("bot stopped")
        sys.exit(0)

    signal.signal(signal.SIGINT, lambda sig, frame: signal_handler(sig, frame, updater.stop, users))


    return users, sender
