from fastapi import APIRouter, Depends, Form, HTTPException
from fastapi.concurrency import run_in_threadpool
from pydantic import ValidationError
from applications.middleware.super_admin import is_super_admin
import libs.lb_config as lb_config
from modules.md_message_broker.dto import MessageBrokerDTO
import modules.md_message_broker.md_message_broker as md_message_broker


def _optional_port(value: str):
    value = (value or "").strip()
    if not value:
        return None
    if not value.isdigit():
        raise ValueError("Porta non valida")
    return int(value)


class MessageBrokerRouter:
    def __init__(self):
        self.router = APIRouter()

        self.router.add_api_route('', self.getMessageBroker, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.setMessageBroker, methods=['POST'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('', self.deleteMessageBroker, methods=['DELETE'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/test', self.testMessageBroker, methods=['GET'], dependencies=[Depends(is_super_admin)])
        self.router.add_api_route('/retry-failed', self.retryFailed, methods=['POST'], dependencies=[Depends(is_super_admin)])

    def _response(self):
        module = md_message_broker.module_message_broker
        settings = md_message_broker.get_settings()
        broker = settings.get("broker")
        if broker:
            # Campi delle vecchie versioni (autenticazione manuale) non più usati
            broker = {k: v for k, v in broker.items() if k not in ("username", "password")}
        config = module.config
        return {
            "broker": broker,
            # Porte effettive (quelle automatiche se nel campo non è indicata nessuna porta)
            "mqtt_port": config.mqtt_port if config else None,
            "registration_port": config.registration_port if config else None,
            "client_id": module.client_id,
            "topic": module.client_id,
            "certificates": module.get_certificates_info(),
        }

    async def getMessageBroker(self):
        return self._response()

    async def setMessageBroker(
        self,
        host: str = Form(...),
        port: str = Form(""),
        enroll_port: str = Form(""),
        include_images: bool = Form(True),
        include_pdf: bool = Form(True),
        include_csv: bool = Form(True),
        remote_ssh: bool = Form(True),
        ssh_user: str = Form("root"),
        ssh_port: int = Form(22),
    ):
        try:
            # Porte vuote = automatiche (443 con un dominio, 8883/8884 con un IP)
            port = _optional_port(port)
            enroll_port = _optional_port(enroll_port)
            body = MessageBrokerDTO(
                host=host, port=port, enroll_port=enroll_port,
                include_images=include_images, include_pdf=include_pdf, include_csv=include_csv,
                remote_ssh=remote_ssh, ssh_user=ssh_user, ssh_port=ssh_port,
            )
        except ValueError as e:
            if isinstance(e, ValidationError):
                raise HTTPException(status_code=400, detail=e.errors()[0]["msg"].replace("Value error, ", ""))
            raise HTTPException(status_code=400, detail=str(e))

        # Salva e prova a collegarsi: se manca il certificato l'in-out si registra sul broker
        module = md_message_broker.module_message_broker
        connected = await run_in_threadpool(module.set_config, body)
        md_message_broker.get_settings()["broker"] = body.model_dump()
        lb_config.saveconfig()
        return {
            **self._response(),
            "connected": connected,
            "status": module.get_status(),
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
