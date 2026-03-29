from typing import Any, List, Dict, Tuple
import re
import threading
import time

from app.core.config import settings
from app.core.event import eventmanager
from app.log import logger
from app.plugins import _PluginBase
from app.schemas.types import EventType
from app.utils.http import RequestUtils


class UnifiedPushNotifier(_PluginBase):
    # 插件元数据
    plugin_name = "统一推送服务"
    plugin_desc = "将MoviePilot事件推送到自定义的统一推送服务（支持标题/内容模板、Token认证）"
    plugin_icon = "webhook.png
    plugin_version = "1.1"
    plugin_author = "WINGS"
    author_url = "https://github.com/yourname"
    plugin_config_prefix = "webhook_push_"
    plugin_order = 15
    auth_level = 1

    # 私有配置
    _enabled = False
    _base_url = ""
    _token = ""
    _token_location = "path"
    _push_path = "/api/push"
    _method = "POST"
    _title_template = "{event_type}"
    _content_template = "{data}"
    _msg_type = "text"
    _event_filters = []
    _timeout = 10
    _retry_times = 2

    def init_plugin(self, config: dict = None):
        super().init_plugin(config)  # 调用父类初始化
        if config:
            self._enabled = config.get("enabled", False)
            self._base_url = config.get("base_url", "").rstrip('/')
            self._token = config.get("token", "")
            self._token_location = config.get("token_location", "path")
            self._push_path = config.get("push_path", "/api/push")
            self._method = config.get("request_method", "POST")
            self._title_template = config.get("title_template", "{event_type}")
            self._content_template = config.get("content_template", "{data}")
            self._msg_type = config.get("msg_type", "text")
            self._event_filters = config.get("event_filters", [])
            self._timeout = int(config.get("timeout", 10))
            self._retry_times = int(config.get("retry_times", 2))

    def get_state(self) -> bool:
        return self._enabled

    @staticmethod
    def get_command() -> List[Dict[str, Any]]:
        return []  # 无命令注册，返回空列表

    def get_api(self) -> List[Dict[str, Any]]:
        return []  # 无API接口，返回空列表

    def get_form(self) -> Tuple[List[dict], Dict[str, Any]]:
        """构建配置表单"""
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
                                        'props': {
                                            'model': 'enabled',
                                            'label': '启用插件',
                                        }
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
                                'props': {'cols': 12, 'md': 8},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'base_url',
                                            'label': '服务基础地址',
                                            'placeholder': '例如 http://192.168.1.2:818',
                                            'required': True
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 4},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'push_path',
                                            'label': '推送路径',
                                            'placeholder': '/api/push'
                                        }
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
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'token',
                                            'label': '接口令牌(Token)',
                                            'required': True
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 6},
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'token_location',
                                            'label': 'Token位置',
                                            'items': ['path', 'header']
                                        }
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
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'request_method',
                                            'label': '请求方式',
                                            'items': ['POST', 'GET']
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VSelect',
                                        'props': {
                                            'model': 'msg_type',
                                            'label': '消息类型',
                                            'items': ['text', 'markdown', 'html']
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'timeout',
                                            'label': '请求超时(秒)',
                                            'type': 'number'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12, 'md': 3},
                                'content': [
                                    {
                                        'component': 'VTextField',
                                        'props': {
                                            'model': 'retry_times',
                                            'label': '重试次数',
                                            'type': 'number',
                                            'min': 0,
                                            'max': 5
                                        }
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
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'title_template',
                                            'label': '标题模板',
                                            'rows': 2,
                                            'placeholder': '支持变量：{event_type}、{data.xxx}，如 {event_type} - {data.title}'
                                        }
                                    }
                                ]
                            },
                            {
                                'component': 'VCol',
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VTextarea',
                                        'props': {
                                            'model': 'content_template',
                                            'label': '内容模板',
                                            'rows': 4,
                                            'placeholder': '支持变量：{event_type}、{data.xxx}，也可使用 {data} 输出全部数据'
                                        }
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
                                'props': {'cols': 12},
                                'content': [
                                    {
                                        'component': 'VCombobox',
                                        'props': {
                                            'model': 'event_filters',
                                            'label': '仅推送以下事件（留空则推送所有）',
                                            'items': [e.value for e in EventType],
                                            'multiple': True,
                                            'chips': True
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
            "base_url": "",
            "token": "",
            "token_location": "path",
            "push_path": "/api/push",
            "request_method": "POST",
            "msg_type": "text",
            "title_template": "{event_type}",
            "content_template": "{data}",
            "event_filters": [],
            "timeout": 10,
            "retry_times": 2
        }

    def get_page(self) -> List[dict]:
        return []  # 无额外页面

    def _safe_to_dict(self, obj: Any, _depth: int = 0) -> Any:
        """安全地将对象转换为字典/基本类型，避免循环引用和过深嵌套"""
        if _depth > 10:
            return str(obj)
        if isinstance(obj, dict):
            return {k: self._safe_to_dict(v, _depth+1) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._safe_to_dict(i, _depth+1) for i in obj]
        elif isinstance(obj, tuple):
            return tuple(self._safe_to_dict(i, _depth+1) for i in obj)
        elif isinstance(obj, set):
            return [self._safe_to_dict(i, _depth+1) for i in obj]
        elif hasattr(obj, 'to_dict'):
            return self._safe_to_dict(obj.to_dict(), _depth+1)
        elif hasattr(obj, '__dict__'):
            return self._safe_to_dict({k: v for k, v in obj.__dict__.items() if not k.startswith('_')}, _depth+1)
        elif isinstance(obj, (int, float, str, bool, type(None))):
            return obj
        else:
            return str(obj)

    def _render_template(self, template: str, event_type: str, event_data: dict) -> str:
        """渲染模板，支持 {event_type} 和 {data.xxx.yyy} 语法"""
        if not template:
            return ""
        result = template.replace("{event_type}", event_type)
        pattern = r"{data\.([^}]+)}"
        for match in re.findall(pattern, result):
            keys = match.split('.')
            value = event_data
            try:
                for key in keys:
                    if isinstance(value, dict):
                        value = value.get(key, "")
                    else:
                        value = ""
                        break
            except Exception:
                value = ""
            result = result.replace(f"{{data.{match}}}", str(value))
        if "{data}" in result:
            result = result.replace("{data}", str(event_data))
        return result.strip()

    def _send_push(self, url: str, headers: dict, payload: dict, retry: int = 0) -> bool:
        """发送推送请求，带指数退避重试"""
        try:
            if self._method == 'POST':
                resp = RequestUtils(headers=headers, timeout=self._timeout).post_res(url, json=payload)
            else:
                resp = RequestUtils(headers=headers, timeout=self._timeout).get_res(url, params=payload)
            if resp and resp.status_code == 200:
                resp_json = resp.json()
                if resp_json.get("success"):
                    logger.info(f"统一推送成功: {url}")
                    return True
                else:
                    logger.warning(f"推送返回失败: {resp_json.get('message')}")
                    return False
            elif resp:
                logger.error(f"推送失败，状态码: {resp.status_code}, 响应: {resp.text}")
                return False
            else:
                logger.error("推送失败，未获取到响应")
                return False
        except Exception as e:
            logger.error(f"推送请求异常: {e}")
            if retry < self._retry_times:
                delay = 2 ** retry
                logger.info(f"重试第 {retry+1} 次，等待 {delay} 秒...")
                time.sleep(delay)
                return self._send_push(url, headers, payload, retry+1)
            return False

    @eventmanager.register(EventType)
    def send_event(self, event):
        """事件处理入口"""
        if not self._enabled or not self._base_url or not self._token:
            return

        # 事件过滤
        version = getattr(settings, "VERSION_FLAG", "v1")
        event_type = event.event_type if version == "v1" else event.event_type.value
        if self._event_filters and event_type not in self._event_filters:
            logger.debug(f"跳过未过滤事件: {event_type}")
            return

        try:
            event_data = self._safe_to_dict(event.event_data)
        except Exception as e:
            logger.error(f"事件数据转换失败: {e}")
            event_data = {}

        title = self._render_template(self._title_template, event_type, event_data)
        content = self._render_template(self._content_template, event_type, event_data)

        if not content:
            logger.warning("渲染后的内容为空，取消推送")
            return

        payload = {
            "title": title[:200] if title else "",
            "content": content[:5000],
            "type": self._msg_type
        }

        # 安全拼接 URL
        base = self._base_url.rstrip('/')
        path = self._push_path.lstrip('/')
        if self._token_location == "path":
            full_url = f"{base}/{path}/{self._token}"
        else:
            full_url = f"{base}/{path}"

        headers = {"Content-Type": "application/json"}
        if self._token_location == "header":
            headers["Authorization"] = f"Bearer {self._token}"

        def async_send():
            self._send_push(full_url, headers, payload)

        threading.Thread(target=async_send, daemon=True).start()

    def stop_service(self):
        """插件停止时清理资源"""
        self._enabled = False
        logger.info("统一推送服务已停止")
