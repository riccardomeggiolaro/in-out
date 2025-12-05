"""
Legacy wrapper functions for panel and siren (DEPRECATED).

These functions are deprecated and maintained only for backward compatibility.
Use the adapter system directly via PanelSirenRouter instead.
"""

import warnings
import applications.router.anagrafic.panel_siren.functions.panel as panel
import applications.router.anagrafic.panel_siren.functions.siren as siren
import libs.lb_config as lb_config


async def send_panel_message(data):
    """
    Send message to panel (DEPRECATED).

    Use PanelSirenRouter.sendMessagePanel() instead.
    """
    warnings.warn(
        "send_panel_message is deprecated. Use PanelSirenRouter.sendMessagePanel() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    await panel.send_message(
        ip=lb_config.g_config["app_api"]["panel"]["ip"],
        port=lb_config.g_config["app_api"]["panel"]["port"],
        username=lb_config.g_config["app_api"]["panel"]["username"],
        password=lb_config.g_config["app_api"]["panel"]["password"],
        timeout=lb_config.g_config["app_api"]["panel"]["timeout"],
        endpoint=lb_config.g_config["app_api"]["panel"]["endpoint"],  # Fixed: was using "siren"
        message=data,
    )


async def send_siren_message():
    """
    Send message to siren (DEPRECATED).

    Use PanelSirenRouter.sendMessageSiren() instead.
    """
    warnings.warn(
        "send_siren_message is deprecated. Use PanelSirenRouter.sendMessageSiren() instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    await siren.send_message(
        ip=lb_config.g_config["app_api"]["siren"]["ip"],
        port=lb_config.g_config["app_api"]["siren"]["port"],
        username=lb_config.g_config["app_api"]["siren"]["username"],
        password=lb_config.g_config["app_api"]["siren"]["password"],
        timeout=lb_config.g_config["app_api"]["siren"]["timeout"],
        endpoint=lb_config.g_config["app_api"]["siren"]["endpoint"],
    )
