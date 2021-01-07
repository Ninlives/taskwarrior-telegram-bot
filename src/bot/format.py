from typing import Union, List
from tasklib.task import Task, TaskQuerySet
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from .constant import *
from datetime import datetime
from math import floor


def task2str(task):
    def sec2time(seconds):
        abssec = abs(seconds)
        one_hour = 60 * 60
        one_day = 24 * one_hour
        days = floor(abssec / one_day)
        hours = floor((abssec - days * one_day) / one_hour)
        return f"{'-' if seconds < 0 else ''}{f'{days}d' if days > 0 else ''}{hours}h"
    result = f"{task['id']}. {task['description']}"

    if task['due']:
        due = task['due'] - datetime.now(task['due'].tzinfo)
        result = result + " ⏱" + sec2time(due.total_seconds())
    # if len(result) > 30:
    #     result = result[:30]
    # else:
    #     result = result + '.' * (30 - len(result))
    return result


def task2message(task):
    message = ""
    if task["project"]:
        message = f"{message}<b>Project:</b> {task['project']}\n\n"

    message = f"{message}<b><u>Description:</u></b>\n{task['description']}"
    annotations = task["annotations"]
    if len(annotations) > 0:
        message = f"{message}\n\n<b><u>Annotations:</u></b>"
        for anno in annotations:
            message = f"{message}\n• {anno['description']}"

    tags = task["tags"]
    if len(tags) > 0:
        message = f"{message}\n\n<b><u>Tags:</u></b>\n{','.join(tags)}"
    return message


def tasks2inlineKeyboard(
    tasks: Union[List[Task], TaskQuerySet]
) -> List[List[InlineKeyboardButton]]:
    sort_by_urgency = sorted(tasks, key=lambda t: t["urgency"])

    def symbol(n, s):
        if n < 3:
            return VERY_URGENT + s
        elif n < 5:
            return URGENT + s
        else:
            return s

    return [
        [InlineKeyboardButton(symbol(len(sort_by_urgency) - n - 1, task2str(task)), callback_data=str(task["id"]))]
        for n, task in enumerate(sort_by_urgency)
    ]


def filters2text(filters: dict) -> str:
    max_len = max([len(k) for k in filters])
    return "\n".join([f"{k:<{max_len}}: {filters[k]}" for k in filters])
