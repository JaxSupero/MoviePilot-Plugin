from typing import Any, List, Dict, Tuple, Optional

from app.core.config import settings
from app.core.event import eventmanager, Event
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType, NotificationType
from app.utils.http import RequestUtils


class WebHookv2(_PluginBase):
    # 插件基本信息【按要求固定】
    plugin_name = "WebHookv2"
    plugin_desc = "MoviePilot V2 系统通知推送至自定义接口，支持Bearer/PathToken，POST/GET"
    plugin_icon = "webhook.png"
    plugin_version = "2.1"
    plugin_author = "WINGS"
    author_url = ""
    plugin_config_prefix = "webhookv2"
    plugin_order = 14
    auth_level = 1

    # 配置项
    _enabled: bool = False
    _api_base: str = ""
    _token: str = ""
    _auth_mode: str = "bearer"
    _send_mode: str = "post"
    _msg_type: str = "text"

    def init_plugin(self, config: dict = None):
        # V2 版本判断
        self.version = settings.VERSION_FLAG if hasattr(settings, "VERSION_FLAG") else "v1"
        if config:
            self._enabled = config.get("enabled", False)
            self._api_base = config.get("api_base", "").strip()
            self._token = config.get("token", "").strip()
            self._auth_mode = config.get("auth_mode", "bearer")
            self._send_mode = config.get("send_mode", "post")
            self._msg_type = config.get("msg_type", "text")

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        return [
            {
                "component": "VForm",
                "content": [
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12},
                                "content": [
                                    {
                                        "component": "VSwitch",
                                        "props": {
                                            "model": "enabled",
                                            "label": "启用插件",
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 7},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "api_base",
                                            "label": "接口基础地址",
                                            "placeholder": "http://192.168.1.2:818"
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 5},
                                "content": [
                                    {
                                        "component": "VTextField",
                                        "props": {
                                            "model": "token",
                                            "label": "接口令牌 Token",
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "component": "VRow",
                        "content": [
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSelect",
                                        "props": {
                                            "model": "auth_mode",
                                            "label": "Token 位置",
                                            "items": [
                                                {"title": "Bearer Header", "value": "bearer"},
                                                {"title": "URL Path", "value": "path"}
                                            ]
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSelect",
                                        "props": {
                                            "model": "send_mode",
                                            "label": "请求方式",
                                            "items": [
                                                {"title": "POST JSON", "value": "post"},
                                                {"title": "GET 参数", "value": "get"}
                                            ]
                                        }
                                    }
                                ]
                            },
                            {
                                "component": "VCol",
                                "props": {"cols": 12, "md": 4},
                                "content": [
                                    {
                                        "component": "VSelect",
                                        "props": {
                                            "model": "msg_type",
                                            "label": "消息类型",
                                            "items": [
                                                {"title": "text", "value": "text"},
                                                {"title": "markdown", "value": "markdown"},
                                                {"title": "html", "value": "html"}
                                            ]
                                        }
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
        ], {
            "enabled": False,
            "api_base": "http://192.168.1.2:818",
            "token": "",
            "auth_mode": "bearer",
            "send_mode": "post",
            "msg_type": "text"
        }

    def get_page(self) -> List[dict]:
        return []

    @eventmanager.register(EventType.NoticeMessage)
    def handle_notify(self, event: Event):
        if not self._enabled or not self._api_base or not self._token:
            return

        data = event.event_data or {}
        logger.info(f"通知事件数据：{data}")

        # ========================
        # 【V2 修复】正确获取标题和内容
        # ========================
        title = data.get("title") or data.get("message_title") or "MoviePilot 通知"
        text = data.get("text") or data.get("message_content") or ""
        msg_type = data.get("type")

        # 空内容直接跳过
        if not text:
            logger.info("跳过空消息通知")
            return

        # 强制使用合法的消息类型（解决类型错误）
        if msg_type not in ["text", "markdown", "html"]:
            msg_type = self._msg_type

        self._push(title, text, msg_type)

    def _push(self, title: str, content: str, msg_type: str):
        base = self._api_base.rstrip("/")
        token = self._token

        # 严格按照接口要求组装JSON
        payload = {
            "title": title,
            "content": content,
            "type": msg_type
        }
        headers = {}

        try:
            # 推荐方式：Bearer + POST
            if self._auth_mode == "bearer" and self._send_mode == "post":
                url = f"{base}/api/push"
                headers["Authorization"] = f"Bearer {token}"
                headers["Content-Type"] = "application/json"
                ret = RequestUtils(headers=headers).post_res(url, json=payload)

            # Path Token + POST
            elif self._auth_mode == "path" and self._send_mode == "post":
                url = f"{base}/api/push/{token}"
                headers["Content-Type"] = "application/json"
                ret = RequestUtils(headers=headers).post_res(url, json=payload)

            # Path Token + GET
            elif self._auth_mode == "path" and self._send_mode == "get":
                url = f"{base}/api/push/{token}"
                ret = RequestUtils().get_res(url, params=payload)

            else:
                logger.warning("不支持的推送模式组合")
                return

            self._parse_result(ret)

        except Exception as e:
            logger.error(f"推送异常: {str(e)}")

    def _parse_result(self, ret: Any):
        if not ret:
            logger.error("推送失败：接口无响应")
            return
        try:
            res = ret.json()
        except Exception:
            logger.error(f"返回非JSON: {ret.text[:200]}")
            return

        success = res.get("success", False)
        code = res.get("code")
        msg = res.get("message", "")
        if success:
            logger.info(f"推送成功 [{code}]: {msg}")
        else:
            logger.error(f"推送失败 [{code}]: {msg}")

    def stop_service(self):
        pass
