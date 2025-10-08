from fastapi import Request, HTTPException
from typing import Dict, Union
from libs.multi_language_messages import multi_language_data
from pathlib import Path

base_path_applications = None

async def get_query_params(request: Request) -> Dict[str, Union[str, int]]:
	"""
	Converts URL query parameters into a dictionary
	"""
	return dict(request.query_params)

# Funzione di validazione per time
async def validate_time(time: Union[int, float]) -> Union[int, float]:
    if time <= 0:
        raise HTTPException(status_code=400, detail="Time must be greater than 0")
    return time

def has_non_none_value(d):
    return any(value not in [None, ""] for value in d.values())

def just_locked_message(action_to_do, table_name, username, weigher_name):
    action_to_do = multi_language_data["actions"][action_to_do]["it"]["endless"]
    table = multi_language_data["table_names"][table_name]["it"]["with_article"]
    message = f"Non puoi {action_to_do} {table} perchè"
    if username:
        message += f" ci sono delle modifiche in corso da parte di '{username}'"
    if weigher_name:
        message += f" è in uso sulla pesa '{weigher_name}'"
    return message