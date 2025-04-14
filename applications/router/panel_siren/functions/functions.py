import applications.router.panel_siren.functions.panel as panel
import applications.router.panel_siren.functions.siren as siren
import libs.lb_config as lb_config

def send_panel_message(data):
    panel.send_message(
        ip=lb_config.g_config["app_api"]["panel"]["ip"],
        port=lb_config.g_config["app_api"]["panel"]["port"],
        username=lb_config.g_config["app_api"]["panel"]["username"],
        password=lb_config.g_config["app_api"]["panel"]["password"],
        timeout=lb_config.g_config["app_api"]["panel"]["timeout"],
        endpoint=lb_config.g_config["app_api"]["siren"]["endpoint"],
        message=data
    )
    
def send_siren_message():
    siren.send_message(
        ip=lb_config.g_config["app_api"]["siren"]["ip"],
        port=lb_config.g_config["app_api"]["siren"]["port"],
        username=lb_config.g_config["app_api"]["siren"]["username"],
        password=lb_config.g_config["app_api"]["siren"]["password"],
        timeout=lb_config.g_config["app_api"]["siren"]["timeout"],
        endpoint=lb_config.g_config["app_api"]["siren"]["endpoint"]
    )