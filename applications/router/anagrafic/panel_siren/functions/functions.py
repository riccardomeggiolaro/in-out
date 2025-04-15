import applications.router.anagrafic.panel_siren.functions.panel as panel
import applications.router.anagrafic.panel_siren.functions.siren as siren
import libs.lb_config as lb_config

async def send_panel_message(data):
    await panel.send_message(
        ip=lb_config.g_config["app_api"]["panel"]["ip"],
        port=lb_config.g_config["app_api"]["panel"]["port"],
        username=lb_config.g_config["app_api"]["panel"]["username"],
        password=lb_config.g_config["app_api"]["panel"]["password"],
        timeout=lb_config.g_config["app_api"]["panel"]["timeout"],
        endpoint=lb_config.g_config["app_api"]["siren"]["endpoint"],
        message=data
    )
    
async def send_siren_message():
    await siren.send_message(
        ip=lb_config.g_config["app_api"]["siren"]["ip"],
        port=lb_config.g_config["app_api"]["siren"]["port"],
        username=lb_config.g_config["app_api"]["siren"]["username"],
        password=lb_config.g_config["app_api"]["siren"]["password"],
        timeout=lb_config.g_config["app_api"]["siren"]["timeout"],
        endpoint=lb_config.g_config["app_api"]["siren"]["endpoint"]
    )