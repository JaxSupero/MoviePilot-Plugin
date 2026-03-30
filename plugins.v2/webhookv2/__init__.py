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
    plugin_version = "2.3"
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
from typing import Any, List, Dict, Tuple

from app.core.config import settings
from app.core.event import eventmanager
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType
from app.utils.http import RequestUtils


class WebHook(_PluginBase):
    # 插件基础信息
    plugin_name = "Webhook"
    plugin_desc = "系统事件触发时，向第三方地址发送HTTP请求"
    plugin_icon = "webhook.png"
    plugin_version = "1.2"
    plugin_author = "jxxghp"
    author_url = "https://github.com/jxxghp"
    plugin_config_prefix = "webhook_"
    plugin_order = 14
    auth_level = 1

    # 私有属性 - 增加默认值
    _enabled: bool = False
    _webhook_url: str = ""
    _method: str = "POST"
    # 请求超时时间（秒）
    _timeout: int = 10

    def init_plugin(self, config: dict = None):
        """初始化插件配置"""
        if not config:
            return
        self._enabled = config.get("enabled", False)
        self._webhook_url = config.get("webhook_url", "").strip()
        self._method = config.get("request_method", "POST").upper()

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []

    def get_api(self) -> List[Dict[str, Any]]:
        return []

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """拼装插件配置页面"""
        request_options = ["POST", "GET"]
        return [
            {
                'component': 'VForm',
                'content': [
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VSwitch',
                                        'props': {'model': 'enabled', 'label': '启用插件'}
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        'component': 'VRow',
                        'content': [
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 4},
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'request_method',
                                            'label': '请求方式',
                                            'items': request_options
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 8},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'webhook_url',
                                            'label': 'WebHook 接收地址',
                                            'placeholder': 'https://example.com/webhook'
                                        }
                                    }
                                ]
                            }
                        ]
                    },
                ]
            }
        ], {
            "enabled": False,
            "request_method": "POST",
            "webhook_url": ""
        }

    def get_page(self) -> List[dict]:
        return []

    @eventmanager.register(EventType)
    def send(self, event):
        """事件触发时发送WebHook请求"""
        # 1. 基础校验
        if not self._enabled or not self._webhook_url:
            return
        if not event or not event.event_type:
            return

        # 2. 递归转换对象为字典（简化版）
        def to_dict(obj: Any) -> Any:
            if isinstance(obj, (dict, list, tuple, set)):
                if isinstance(obj, dict):
                    return {k: to_dict(v) for k, v in obj.items()}
                elif isinstance(obj, (list, tuple)):
                    return [to_dict(i) for i in obj]
                elif isinstance(obj, set):
                    return [to_dict(i) for i in obj]
            if hasattr(obj, "to_dict"):
                return to_dict(obj.to_dict())
            if hasattr(obj, "__dict__"):
                return to_dict(obj.__dict__)
            if isinstance(obj, (int, float, str, bool, type(None))):
                return obj
            return str(obj)

        # 3. 构建事件数据
        event_data = to_dict(event.event_data)
        event_type = event.event_type.value if hasattr(event.event_type, 'value') else event.event_type
        
        payload = {
            "event": event_type,
            "data": event_data,
            "version": getattr(settings, "VERSION_FLAG", "unknown")
        }

        # 4. 发送HTTP请求
        try:
            if self._method == "POST":
                # POST：JSON格式请求
                response = RequestUtils(
                    content_type="application/json",
                    timeout=self._timeout
                ).post_res(self._webhook_url, json=payload)
            else:
                # GET：扁平化参数请求（适配URL参数）
                get_params = {"event": payload["event"]}
                if isinstance(payload["data"], dict):
                    get_params.update(payload["data"])
                response = RequestUtils(timeout=self._timeout).get_res(self._webhook_url, params=get_params)

            # 5. 结果处理
            if response and response.ok:
                logger.info(f"WebHook 请求成功 | 地址：{self._webhook_url} | 事件：{event_type}")
            elif response:
                logger.error(f"WebHook 请求失败 | 状态码：{response.status_code} | 响应：{response.text[:100]}")
            else:
                logger.error(f"WebHook 请求失败 | 地址：{self._webhook_url} | 无响应")

        except Exception as e:
            logger.error(f"WebHook 请求异常 | 原因：{str(e)}", exc_info=True)

    def stop_service(self):
        """插件退出"""
        pass
