from fastapi import Request, HTTPException
from typing import Dict, Union
from libs.multi_language_messages import multi_language_data
import pandas as pd
import base64
import mimetypes

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

def convert_value(x, expected_type):
    if pd.isna(x):
        return x
    # Se il tipo atteso è stringa e il valore è numerico, convertilo in stringa
    if expected_type is str and isinstance(x, (int, float)):
        return str(x)
    return x

def image_to_base64_data_uri(image_path):
    """
    Converte un'immagine in data URI base64 completo
    
    Args:
        image_path (str): Percorso del file immagine
        
    Returns:
        str: Data URI completo (es: data:image/png;base64,...)
    """
    # Determina il MIME type
    mime_type, _ = mimetypes.guess_type(image_path)
    if mime_type is None:
        mime_type = 'application/octet-stream'
    
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    
    return f"data:{mime_type};base64,{encoded_string}"