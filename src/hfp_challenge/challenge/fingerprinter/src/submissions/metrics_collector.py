import logging
from typing import Any

logger = logging.getLogger(__name__)


def preprocess_metrics(raw_metrics: dict[str, Any]) -> dict[str, Any]:
    payload = {}

    products = raw_metrics.get("products", {})
    identification = products.get("identification", {}).get("data", {})
    raw_device = products.get("rawDeviceAttributes", {}).get("data", {})

    user_agent = identification.get("userAgent") or identification.get("browserDetails", {}).get("userAgent")
    if user_agent:
        payload["user_agent"] = user_agent.lower().strip()

    browser_details = identification.get("browserDetails", {})
    payload["browser_name"] = browser_details.get("browserName", "").lower()
    payload["browser_version"] = browser_details.get("browserFullVersion", "")
    payload["os"] = browser_details.get("os", "").lower()
    payload["os_version"] = browser_details.get("osVersion", "")
    payload["device"] = browser_details.get("device", "")

    ip_info = products.get("ipInfo", {}).get("data", {})
    if ip_info.get("v4"):
        payload["ip_address"] = ip_info["v4"].get("address")
    elif ip_info.get("v6"):
        payload["ip_address"] = ip_info["v6"].get("address")

    payload["incognito"] = products.get("incognito", {}).get("data", {}).get("result", False)

    botd = products.get("botd", {}).get("data", {})
    payload["bot_result"] = botd.get("bot", {}).get("result", "unknown")

    canvas = raw_device.get("canvas", {}).get("value", {})
    if isinstance(canvas, dict):
        payload["canvas_geometry"] = canvas.get("Geometry", "")
        payload["canvas_text"] = canvas.get("Text", "")

    audio = raw_device.get("audio", {}).get("value")
    if audio is not None:
        payload["audio_hash"] = str(audio)[:16]

    cpu = raw_device.get("cpuClass", {}).get("value")
    if cpu:
        payload["cpu_class"] = str(cpu)

    architecture = raw_device.get("architecture", {}).get("value")
    if architecture is not None:
        payload["architecture"] = str(architecture)

    color_depth = raw_device.get("colorDepth", {}).get("value")
    if color_depth is not None:
        payload["color_depth"] = color_depth

    color_gamut = raw_device.get("colorGamut", {}).get("value")
    if color_gamut:
        payload["color_gamut"] = color_gamut.lower()

    contrast = raw_device.get("contrast", {}).get("value")
    if contrast is not None:
        payload["contrast"] = contrast

    fonts = raw_device.get("fonts", {}).get("value")
    if fonts and isinstance(fonts, list):
        payload["fonts"] = ",".join(sorted(fonts))

    cookies_enabled = raw_device.get("cookiesEnabled", {}).get("value")
    if cookies_enabled is not None:
        payload["cookies_enabled"] = cookies_enabled

    vpn = products.get("vpn", {}).get("data", {})
    payload["vpn_detected"] = vpn.get("result", False)

    proxy = products.get("proxy", {}).get("data", {})
    payload["proxy_detected"] = proxy.get("result", False)

    datacenter_v4 = ip_info.get("v4", {}).get("datacenter", {}).get("result", False)
    datacenter_v6 = ip_info.get("v6", {}).get("datacenter", {}).get("result", False)
    payload["is_datacenter"] = datacenter_v4 or datacenter_v6

    logger.info(f"Preprocessed metrics: {list(payload.keys())}")
    return payload


__all__ = ["preprocess_metrics"]
