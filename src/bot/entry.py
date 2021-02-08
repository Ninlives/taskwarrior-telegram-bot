import sys
import logging
import threading
import time
from lib import updator

from tasklib import TaskWarrior
from telegram import (
    Bot,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ParseMode,
    MessageEntity
)
from telegram.ext.filters import Filters

from .constant import *
from .format import *
from lib.updator import *

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

_tw = None
_filters = None
_tw_lock = threading.Lock()

class syncThread(threading.Thread):
    def run(self):
        while True:
            _tw_lock.acquire()
            tasks = _tw.tasks.filter(status='pending')
            _tw.sync()
            _tw_lock.release()
            time.sleep(60*60)


class chatThread(threading.Thread):
    def run(self):
        message = get_next_message()
        updator.CHATID = message.chat_id
        self.listen()
    
    
    def listen(self):
        while True:
            commands = {
                "List all tasks": lambda: self.list_task(self.edit_task),
                "Add a new task": self.add_task,
            }
            keyboard = [[KeyboardButton(c) for c in commands]]
            send_message("I'm listening.", reply_markup=ReplyKeyboardMarkup(keyboard))
            message = get_next_message()
    
            _tw_lock.acquire()
            _tw.sync()
            if (
                message.entities
                and message.entities[0].type == MessageEntity.BOT_COMMAND
                and message.entities[0].offset == 0
            ):
                args = message.text.split()[1:]
                command = message.text[1 : message.entities[0].length].split('@')[0]
                self.handle_command(command, args)
            else:
                for c in commands:
                    if Filters.text(c).filter(message):
                        commands[c]()
                        break
            _tw.sync()
            _tw_lock.release()
    
    def handle_command(self, command, args):
        if command == 'task':
            send_message('\n'.join(_tw.execute_command(args)).strip())
        else:
            send_message("Unsupported command.")
    
    def list_task(self, callback, finish_label="Finish", replace_message=None):
        global _filters
        filters = _filters if _filters else {"status": "pending"}
    
        tasks = _tw.tasks.filter(**filters)
        keyboard = tasks2inlineKeyboard(tasks) + [
            [
                InlineKeyboardButton("Edit filters", callback_data=CB_EDIT_FILTER),
                InlineKeyboardButton(finish_label, callback_data=CB_FINISH),
            ]
        ]
        text = f"Using filters:\n{filters2text(filters)}"
        markup = InlineKeyboardMarkup(keyboard)
    
        if replace_message:
            rep_message = replace_message.edit_text(text, reply_markup=markup)
        else:
            rep_message = send_message(text, reply_markup=markup)
    
        if rep_message == None:
            return None
    
        reply = get_next_callbackquery(rep_message)
        if reply.data == CB_EDIT_FILTER:
            reply.edit_message_text("Edit filters is not implemented")
        else:
            callback(reply)
    
    
    def add_task(self):
        send_message(
            "Send description for new task.",
            reply_markup=ReplyKeyboardMarkup([[KeyboardButton("# CANCEL OPERATION")]]),
        )
        reply = get_next_message()
        if Filters.text("# CANCEL OPERATION").filter(reply):
            send_message("Operation cancelled.")
        else:
            new_task = Task(_tw, description=reply.text)
            send_message(task2message(new_task), parse_mode=ParseMode.HTML)
            if self.confirm("Do you want to create above task?"):
                # Dirty hack for saving
                keys = []
                for attr in new_task.__dict__['_data']:
                    if attr != 'description':
                        keys.append(attr)
                for key in keys:
                    new_task.__dict__['_data'].pop(key)
    
                new_task.save()
                send_message("Task saved.")
            else:
                send_message("Operation cancelled.")
    
    
    def edit_task(self, reply):
        if reply.data == CB_FINISH:
            return
    
        task = _tw.tasks.get(id=reply.data)
        msg = reply.edit_message_text(
            task2message(task),
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Done", callback_data="done"),
                        InlineKeyboardButton("Delete", callback_data="delete"),
                    ],
                    [InlineKeyboardButton("Return", callback_data="return")],
                ]
            ),
        )
    
        while True:
            selection = get_next_callbackquery(msg)
            if selection.data == "return":
                return self.list_task(self.edit_task, replace_message=msg)
            elif selection.data == "done":
                if self.confirm("Are you sure you want to mark this task as 'Done'?"):
                    task.done()
                    edit_reply_markup(msg, reply_markup=InlineKeyboardMarkup([]))
                    return self.list_task(self.edit_task)
                else:
                    send_message("Operation cancelled.")
            elif selection.data == "delete":
                if self.confirm("Are you sure you want to DELETE this task?"):
                    task.delete()
                    edit_reply_markup(msg, reply_markup=InlineKeyboardMarkup([]))
                    return self.list_task(self.edit_task)
                else:
                    send_message("Operation cancelled.")
    
    
    def confirm(self, text):
        while True:
            send_message(
                text,
                reply_markup=ReplyKeyboardMarkup(
                    [[KeyboardButton("Yes"), KeyboardButton("No")]]
                ),
            )
            reply = get_next_message()
            if Filters.text("Yes").filter(reply):
                return True
            if Filters.text("No").filter(reply):
                return False


def main() -> None:
    updator.BOT = Bot(sys.argv[1])
    updator.USER = int(sys.argv[2])
    global _tw
    _tw = TaskWarrior(data_location=sys.argv[3], taskrc_location=sys.argv[4], create=True)
    syncThread().start()
    chatThread().start()
