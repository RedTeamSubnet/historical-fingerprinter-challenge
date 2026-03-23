import logging
from typing import Any

logger = logging.getLogger(__name__)


def preprocess_metrics(raw_metrics: dict[str, Any]) -> dict[str, Any]:
    payload = {}

    raw_device = raw_metrics.get("rawDeviceAttributes", {}).get("data", {})
    if not raw_device:
        raw_device = raw_metrics

    architecture = raw_device.get("architecture", {}).get("value")
    if architecture is not None:
        payload["architecture"] = str(architecture)

    audio = raw_device.get("audio", {}).get("value")
    if audio is not None:
        payload["audio_hash"] = str(audio)[:16]

    canvas = raw_device.get("canvas", {}).get("value", {})
    if isinstance(canvas, dict):
        geometry = canvas.get("geometry", "")
        text = canvas.get("text", "")
        if geometry:
            payload["canvas_geometry"] = geometry[:100]
        if text:
            payload["canvas_text"] = text[:100]
        winding = canvas.get("winding")
        if winding is not None:
            payload["canvas_winding"] = winding

    color_depth = raw_device.get("colorDepth", {}).get("value")
    if color_depth is not None:
        payload["color_depth"] = color_depth

    color_gamut = raw_device.get("colorGamut", {}).get("value")
    if color_gamut:
        payload["color_gamut"] = color_gamut.lower()

    contrast = raw_device.get("contrast", {}).get("value")
    if contrast is not None:
        payload["contrast"] = contrast

    cookies_enabled = raw_device.get("cookiesEnabled", {}).get("value")
    if cookies_enabled is not None:
        payload["cookies_enabled"] = cookies_enabled

    cpu_class = raw_device.get("cpuClass", {}).get("value")
    if cpu_class:
        payload["cpu_class"] = str(cpu_class)

    device_memory = raw_device.get("deviceMemory", {}).get("value")
    if device_memory is not None:
        payload["device_memory"] = device_memory

    fonts = raw_device.get("fonts", {}).get("value")
    if fonts and isinstance(fonts, list):
        payload["fonts"] = ",".join(sorted(fonts))

    font_prefs = raw_device.get("fontPreferences", {}).get("value", {})
    if font_prefs:
        payload["font_preferences"] = str(font_prefs)

    forced_colors = raw_device.get("forcedColors", {}).get("value")
    if forced_colors is not None:
        payload["forced_colors"] = forced_colors

    hardware_concurrency = raw_device.get("hardwareConcurrency", {}).get("value")
    if hardware_concurrency is not None:
        payload["hardware_concurrency"] = hardware_concurrency

    hdr = raw_device.get("hdr", {}).get("value")
    if hdr is not None:
        payload["hdr"] = hdr

    indexed_db = raw_device.get("indexedDB", {}).get("value")
    if indexed_db is not None:
        payload["indexed_db"] = indexed_db

    inverted_colors = raw_device.get("invertedColors", {}).get("value")
    if inverted_colors is not None:
        payload["inverted_colors"] = inverted_colors

    languages = raw_device.get("languages", {}).get("value")
    if languages:
        payload["languages"] = str(languages)

    local_storage = raw_device.get("localStorage", {}).get("value")
    if local_storage is not None:
        payload["local_storage"] = local_storage

    math_values = raw_device.get("math", {}).get("value")
    if math_values and isinstance(math_values, dict):
        math_sample = str(list(math_values.values())[:5])
        payload["math_signature"] = math_sample

    monochrome = raw_device.get("monochrome", {}).get("value")
    if monochrome is not None:
        payload["monochrome"] = monochrome

    open_database = raw_device.get("openDatabase", {}).get("value")
    if open_database is not None:
        payload["open_database"] = open_database

    os_cpu = raw_device.get("osCpu", {}).get("value")
    if os_cpu:
        payload["os_cpu"] = str(os_cpu)

    pdf_viewer_enabled = raw_device.get("pdfViewerEnabled", {}).get("value")
    if pdf_viewer_enabled is not None:
        payload["pdf_viewer_enabled"] = pdf_viewer_enabled

    platform = raw_device.get("platform", {}).get("value")
    if platform:
        payload["platform"] = platform.lower()

    plugins = raw_device.get("plugins", {}).get("value")
    if plugins and isinstance(plugins, list):
        payload["plugins_count"] = len(plugins)

    reduced_motion = raw_device.get("reducedMotion", {}).get("value")
    if reduced_motion is not None:
        payload["reduced_motion"] = reduced_motion

    screen_frame = raw_device.get("screenFrame", {}).get("value")
    if screen_frame and isinstance(screen_frame, list):
        payload["screen_frame"] = ",".join(map(str, screen_frame))

    screen_resolution = raw_device.get("screenResolution", {}).get("value")
    if screen_resolution and isinstance(screen_resolution, list):
        payload["screen_resolution"] = f"{screen_resolution[0]}x{screen_resolution[1]}"

    session_storage = raw_device.get("sessionStorage", {}).get("value")
    if session_storage is not None:
        payload["session_storage"] = session_storage

    timezone = raw_device.get("timezone", {}).get("value")
    if timezone:
        payload["timezone"] = timezone.lower()

    touch_support = raw_device.get("touchSupport", {}).get("value", {})
    if touch_support:
        max_touch = touch_support.get("maxTouchPoints", 0)
        if max_touch is not None:
            payload["max_touch_points"] = max_touch

    vendor = raw_device.get("vendor", {}).get("value")
    if vendor:
        payload["vendor"] = vendor.lower()

    vendor_flavors = raw_device.get("vendorFlavors", {}).get("value")
    if vendor_flavors and isinstance(vendor_flavors, list):
        payload["vendor_flavors"] = ",".join(vendor_flavors)

    video_card = raw_device.get("videoCard", {}).get("value", {})
    if video_card:
        renderer = video_card.get("renderer", "")
        vendor_gpu = video_card.get("vendor", "")
        if renderer:
            payload["gpu_renderer"] = renderer.lower()
        if vendor_gpu:
            payload["gpu_vendor"] = vendor_gpu.lower()

    logger.info(f"Preprocessed metrics: {list(payload.keys())}")
    return payload


__all__ = ["preprocess_metrics"]
