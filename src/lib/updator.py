import logging
import sys
from time import sleep
from telegram.error import NetworkError

BOT = None
USER = None
CHATID = None
logger = logging.getLogger(__name__)
_updates = None
_update_id = None


def send_message(*args, **kwargs):
    return BOT.send_message(CHATID, *args, **kwargs)


def edit_reply_markup(message, *args, **kwargs):
    return BOT.edit_message_reply_markup(
        chat_id=CHATID, message_id=message.message_id, *args, **kwargs
    )


def get_next_update(filter=None):
    logger.info("Get next update.")

    global BOT
    global _update_id
    global _updates

    while True:
        if _updates and len(_updates) > 0:
            update = _updates.pop(0)
            if len(_updates) == 0:
                _update_id = update.update_id + 1

            if update.effective_user.id != USER:
                BOT.send_message(
                    update.effective_chat.id,
                    "I sincerely hope you weren't expecting a response.\nBecause I'm not talking to you.",
                )
                continue

            logger.info(f"Get update: {update}")
            if filter:
                if not filter(update):
                    continue
            return update
        else:
            try:
                sleep(1)
                _updates = BOT.get_updates(offset=_update_id, timeout=10)
            except NetworkError:
                pass
            except KeyboardInterrupt:
                sys.exit(0)


def get_next_message():
    def message(update):
        return update.message != None

    return get_next_update(message).message


def get_next_callbackquery(message):
    while True:
        reply = get_next_update().callback_query
        if reply:
            reply.answer()
            if reply.message.message_id == message.message_id:
                return reply
