from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from applications.middleware.super_admin import is_super_admin
import libs.lb_config as lb_config
from modules.md_message_broker.dto import MessageBrokerDTO
import modules.md_message_broker.md_message_broker as md_message_broker


class MessageBrokerRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('', self.getMessageBroker, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.setMessageBroker, methods=['POST'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.deleteMessageBroker, methods=['DELETE'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/test', self.testMessageBroker, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/retry-failed', self.retryFailed, methods=['POST'], dependencies=[Depends(is_super_admin)])

    async def getMessageBroker(self):
        settings = dict(md_message_broker.get_settings())
        broker = settings.get("broker")
        if broker and broker.get("password"):
            settings["broker"] = {**broker, "password": "********"}
        return settings

    async def setMessageBroker(self, body: MessageBrokerDTO):
        settings = md_message_broker.get_settings()
        # Se la password arriva mascherata (dal GET) si mantiene quella salvata
        if body.password == "********" and settings.get("broker"):
            body.password = settings["broker"].get("password")
        connected = await run_in_threadpool(md_message_broker.module_message_broker.set_config, body)
        settings["broker"] = body.model_dump()
        lb_config.saveconfig()
        return {
            "connected": connected,
            "status": md_message_broker.module_message_broker.get_status(),
        }

    async def deleteMessageBroker(self):
        await run_in_threadpool(md_message_broker.module_message_broker.set_config, None)
        md_message_broker.get_settings()["broker"] = None
        lb_config.saveconfig()
        return {"deleted": True}

    async def testMessageBroker(self):
        return md_message_broker.module_message_broker.get_status()

    async def retryFailed(self):
        count = md_message_broker.module_message_broker.retry_failed()
        return {"requeued": count}
