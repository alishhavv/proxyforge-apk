#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
╔═══════════════════════════════════════════════════════════════════════════════════╗
║  PROXY FORGE v9.0 — ULTIMATE EDITION                                             ║
║                                                                                 ║
║  Автоматический поиск, валидация и ранжирование прокси-конфигураций,            ║
║  устойчивых к DPI-фильтрации, блокировкам РКН и работе в белых списках.        ║
║                                                                                 ║
║  v9.0 CHANGES:                                                                  ║
║    🔥 MERGED: proxy_forge v8 + vpn_hunter v1 + proxy_fetcher v2                ║
║    📊 Clash/Sing-Box YAML output (--clash)                                      ║
║    📦 Base64 subscription output (--b64)                                        ║
║    🔍 Protocol filter (--proto vless,hy2)                                      ║
║    🌍 Country filter (--country RU,DE,US)                                       ║
║    💀 Alive-only filter (--alive-only)                                          ║
║    📈 Sort modes (--sort ping|dpi|country|proto)                                ║
║    📋 Clipboard copy (--copy)                                                    ║
║    📄 JSON export (--json)                                                       ║
║    🔄 Auto-update check (--check-update)                                        ║
║    🛡 Stealth threshold (--stealth-threshold 70)                                ║
║    🌐 DNS resolution cache + hostname resolve (--resolve)                        ║
║    ✅ Config validation (host, port, UUID)                                       ║
║    🔁 Duplicate detection with source tracking                                   ║
║    📊 Source reliability scoring                                                ║
║    🔗 Export working subscription URLs                                           ║
║    🚀 5+ CDN mirror providers                                                    ║
║    🖥 IPv6 support in host parsing and ping                                     ║
║    🎯 Enhanced DPI scoring (xudp, alpn, spx, serviceName)                       ║
║    📡 Multi-ping averaging (--ping-count 3)                                     ║
║    🌐 DNS resolution cache                                                      ║
║    📊 Detailed per-source report                                                ║
║    🗂 Country-grouped output (серв_grouped.txt)                                ║
║    ❤ Health check mode (--health)                                              ║
║    ⭐ Auto-select best config + copy to clipboard                               ║
║    🔇 Quiet mode (--quiet)                                                      ║
║    🔊 Verbose mode (-v/--verbose)                                                ║
║                                                                                 ║
║  Protocols: VLESS (Reality/XHTTP/WS/gRPC), VMess, Trojan, SS, SSR,             ║
║             Hysteria2, TUIC, WireGuard                                          ║
║                                                                                 ║
║  Compatible: v2rayNG / NekoBox / Sing-Box / Hiddify / Clash / v2rayN           ║
║  Runs in Termux (Android) without root, without pip install                    ║
║                                                                                 ║
║  Usage:                                                                         ║
║    python3 proxy_forge.py                   # Full cycle with ping             ║
║    python3 proxy_forge.py --fast            # Without ping (~15 sec)            ║
║    python3 proxy_forge.py --stealth         # DPI-resistant only                ║
║    python3 proxy_forge.py --whitelist       # For RKN whitelist mode            ║
║    python3 proxy_forge.py --top 50          # Top 50 best configs              ║
║    python3 proxy_forge.py --timeout 3       # Ping timeout 3 sec               ║
║    python3 proxy_forge.py --proto vless     # Filter by protocol               ║
║    python3 proxy_forge.py --country RU,DE   # Filter by country                ║
║    python3 proxy_forge.py --alive-only      # Only alive configs               ║
║    python3 proxy_forge.py --sort ping       # Sort by ping                     ║
║    python3 proxy_forge.py --clash           # Clash YAML output                ║
║    python3 proxy_forge.py --b64             # Base64 subscription output       ║
║    python3 proxy_forge.py --json            # JSON export                      ║
║    python3 proxy_forge.py --copy            # Copy to clipboard                ║
║    python3 proxy_forge.py --health          # Health check embedded configs    ║
║    python3 proxy_forge.py --quiet           # Minimal output                   ║
║    python3 proxy_forge.py -v                # Verbose output                  ║
╚═══════════════════════════════════════════════════════════════════════════════════╝
"""

import os
import re
import sys
import json
import socket
import base64
import signal
import threading
import time
import ssl
import struct
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse, parse_qs, unquote, quote
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import OrderedDict

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 1: CONFIGURATION
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MAX_DL_WORKERS = 15
MAX_PING_WORKERS = 50
DL_TIMEOUT = 15
PING_TIMEOUT = 5
PROBE_TIMEOUT = 4
CACHE_MAX_CONFIGS = 5000
STEALTH_DEFAULT_THRESHOLD = 60
DEFAULT_PING_COUNT = 1

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_MAIN = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432")
OUTPUT_RAW = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432_raw.txt")
OUTPUT_STEALTH = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432_stealth.txt")
OUTPUT_WL = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432_whitelist.txt")
OUTPUT_SUB = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432_sub.txt")
OUTPUT_REPORT = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432_report.txt")
OUTPUT_GROUPED = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432_grouped.txt")
OUTPUT_CLASH = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432_clash.yaml")
OUTPUT_B64 = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432_b64.txt")
OUTPUT_JSON = os.path.join(SCRIPT_DIR, "\u0441\u0435\u0440\u0432\u0438_data.json")
CACHE_FILE = os.path.join(SCRIPT_DIR, ".proxy_forge_cache.json")

SUPPORTED_PROTOCOLS = (
    "vless://", "vmess://", "trojan://",
    "ss://", "ssr://",
    "hysteria2://", "hy2://", "hysteria://",
    "tuic://",
    "wg://", "wireguard://",
)

PROTO_NAMES = {
    "vless://": "VLESS", "vmess://": "VMESS", "trojan://": "TROJAN",
    "ss://": "SS", "ssr://": "SSR",
    "hysteria2://": "HYSTERIA2", "hy2://": "HYSTERIA2",
    "hysteria://": "HYSTERIA", "tuic://": "TUIC",
    "wg://": "WIREGUARD", "wireguard://": "WIREGUARD",
}

PROTO_CLASH_NAME = {
    "VLESS": "vless", "VMESS": "vmess", "TROJAN": "trojan",
    "SS": "ss", "SSR": "ssr", "HYSTERIA2": "hysteria2",
    "HYSTERIA": "hysteria", "TUIC": "tuic", "WIREGUARD": "wireguard",
}

PROTO_ICON = {
    "VLESS": "\U0001f7e3", "VMESS": "\U0001f535", "TROJAN": "\U0001f534",
    "SS": "\U0001f7e2", "SSR": "\U0001f7e2", "HYSTERIA2": "\U0001f7e0",
    "HYSTERIA": "\U0001f7e0", "TUIC": "\U0001f7e1", "WIREGUARD": "\u26aa",
}

HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 14; Pixel 8 Pro) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.6422.76 Mobile Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9,ru;q=0.8",
    "Accept-Encoding": "identity",
    "Cache-Control": "no-cache",
    "Connection": "close",
}

LEGITIMATE_SNI = {
    "www.microsoft.com", "www.apple.com", "www.amazon.com",
    "www.google.com", "www.yahoo.com", "www.cloudflare.com",
    "www.facebook.com", "www.twitter.com", "www.github.com",
    "www.linkedin.com", "www.netflix.com", "www.twitch.tv",
    "www.wikipedia.org", "www.reddit.com", "www.stackoverflow.com",
    "browser.yandex.com", "api-maps.yandex.ru", "ya.ru",
    "www.samsung.com", "www.adobe.com", "www.mozilla.org",
    "www.dropbox.com", "www.slack.com", "www.discord.com",
    "api.vk.com", "www.vk.com", "eh.vk.com", "eh.vk.ru",
    "sso.passport.yandex.ru", "static-mon.yandex.net",
    "ads.x5.ru", "rbc.ru",
    "pimg.mycdn.me", "sun6-22.userapi.com",
    "chat.deepseek.com", "www.bing.com", "max.ru",
    "www.vkvideo.ru", "goodcardboard.shop",
    "qbank.ir", "speedtest.net", "black-moai.com",
    "www.black-moai.com", "amazon.com",
}

WHITELIST_SNI = LEGITIMATE_SNI.copy()

CDN_HOSTS = {
    "cloudflare.com", "cloudflare.cn", "workers.dev",
    "akamai.net", "akamaized.net",
    "fastly.net", "fastlylb.net",
    "azureedge.net", "azure.com",
    "googleapis.com", "gstatic.com",
    "amazonaws.com", "cloudfront.net",
    "cdn77.org", "stackpathdns.com",
    "bunnycdn.com", "cdnjs.net",
    "jsdelivr.net", "unpkg.com",
}

WHITELISTED_CDNS = {
    "cloudflare.com", "workers.dev",
    "akamai.net", "akamaized.net",
    "googleapis.com", "gstatic.com",
    "fastly.net", "azureedge.net",
    "amazonaws.com", "cloudfront.net",
    "cdn77.org",
}

# SSL context — no certificate verification (for blocked/censored networks)
_ssl_ctx = ssl.create_default_context()
_ssl_ctx.check_hostname = False
_ssl_ctx.verify_mode = ssl.CERT_NONE

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 2: EMBEDDED EMERGENCY CONFIGS (35 configs)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

EMBEDDED_CONFIGS = [
    "vless://197a0c0a-574d-497a-9e44-7bec185f8662@84.201.173.212:8443?type=tcp&security=reality&encryption=none&flow=xtls-rprx-vision&fp=chrome&pbk=IbBORC7a_sjJeYsjQl85KFsgh1GBEDZDsI5JsxeoaRQ&sid=b81e3a4f&sni=api-maps.yandex.ru#Bulgaria",
    "vless://00400444-4440-4440-8440-044444400400@51.250.99.92:443?type=tcp&security=reality&encryption=none&flow=xtls-rprx-vision&fp=chrome&pbk=Kt_hjy94lr2-zyQhDhGxtPOOrhSmlxOOWcII0X0u-wY&sid=aabbccdd&sni=browser.yandex.com&alpn=h2#Czechia",
    "vless://82b5b465-3307-4a25-acef-abd1649bbedf@fr1.samovargate.com:443?security=reality&encryption=none&pbk=gwuAehnMX6e-n1fxIenfjx43j3qXXi7Cb4wfnW5VyBQ&type=tcp&flow=xtls-rprx-vision&sni=www.microsoft.com&fp=chrome&sid=f04729f65b9ea261#France",
    "vless://2e2abd1f-4b43-420a-a6a9-37b6e8fef206@178.72.171.212:443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=randomized&sni=api-maps.yandex.ru&pbk=7TvkMzoB3gEZy-5HfL6-M_AT_qWVgyeoiggDb2Qg5hE&spx=%2F#Germany",
    "vless://2e2abd1f-4b43-420a-a6a9-37b6e8fef206@178.72.171.212:443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=randomized&sni=eh.vk.com&pbk=P58JPgSU0wIgMZRT7KMiW2gQEWWJHExCLd7f6miNbGA&spx=%2F#Germany",
    "vless://bdaddcff-cc26-43e4-8c88-3e67ee6ee21f@217.13.104.213:443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&sni=sun6-22.userapi.com&pbk=fhMqHujqxaRsM4oM5MOectW90_nHWj7AEftfbO3Ht0Q#Hungary",
    "vless://18e48126-5325-4618-a3f5-fda84003deb4@5.188.115.230:443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=random&sni=ads.x5.ru&pbk=kKiat1UsRVMj7F5APS8MMMDbwFE6fUI5maS3oMsrTgI&sid=27e53bbcab7593d7&spx=%2F#Poland",
    "vless://99e2fd5e-f5b2-47f9-be5a-eb38daa4e670@212.233.97.35:5443?encryption=none&flow=&fp=chrome&packetEncoding=xudp&pbk=wXpc4aufCrdxZ2_aoh6Zt0aLWLioMN2Zi0jtKdonMW4&security=reality&sid=b027c9244d2a&sni=max.ru&type=tcp#Poland",
    "vless://b91ca476-26f1-4dc3-a5e9-57cf457f3499@185.242.16.16:443?encryption=none&type=ws&security=tls&path=%2FgetServiceStatus%2F&host=mullsite.applepie-recipe.ru&sni=mullsite.applepie-recipe.ru#Sweden",
    "vless://a18a8faa-d836-4111-85ab-ad4c5040fafa@212.233.97.128:5443/?type=tcp&encryption=none&flow=&sni=ads.x5.ru&fp=chrome&security=reality&pbk=SskAaq34j0FCgo85shlAWsupaS7DfB_gfaQEqXprqWo&sid=0e5dcb&packetEncoding=xudp#Netherlands",
    "vless://09b81314-7592-4ffb-9773-6351de8a7f74@79.174.95.163:2083?encryption=none&security=reality&sni=ads.x5.ru&fp=qq&pbk=J6NuOlIq3ypdTFc1TMhDDKmF8BWPnNWZq1EkxD7K-lQ&sid=6da16b1335651b38&type=grpc&authority=&serviceName=UpdateService&mode=gun#Russia",
    "vless://2e2abd1f-4b43-420a-a6a9-37b6e8fef206@90.156.224.147:443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=randomized&sni=goodcardboard.shop&pbk=rDPZZOBMmBb_mNKPEewzp9Uu6zkGrP7XOVpnRzetXDc&spx=%2F#Russia",
    "vless://740b321d-e5cb-49cf-9468-1c27f6342e2e@217.16.18.154:443?security=reality&sni=eh.vk.ru&fp=chrome&pbk=LHcascaxOxugVSALgsYx46nB-vuhT7ANOneu0xb6SzQ&sid=f119dce0d6234781&type=tcp&flow=xtls-rprx-vision&packetEncoding=xudp&encryption=none#Russia",
    "vless://56022eef-4ade-4240-b0cc-eb006797e7ac@94.126.207.245:443?type=tcp&security=reality&encryption=none&flow=xtls-rprx-vision&fp=chrome&pbk=V32osv0u9T3QItvyk4UgK-mjJuXkXLn4u_3pbk8eNgs&sid=9339&sni=api.vk.com#Russia",
    "vless://88af3d08-d5e1-4148-89a7-5201146c10a5@94.139.251.109:7443?security=reality&encryption=none&pbk=5QAO98ot2U7TcGs_f6EEaQjCzNOJLNHqPf6smYsdFVI&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=chat.deepseek.com&sid=d82fb387#Russia",
    "vless://a96f18f0-4a56-4c4f-be6e-434835f5523c@51.250.42.3:443?type=tcp&security=reality&encryption=none&flow=xtls-rprx-vision&fp=chrome&pbk=e6QVzqAw4kvQHxdu2pFsLnadziIWm9DjOo2rul_NgAk&sid=8ac77e6b777376f8&sni=ads.x5.ru#Russia",
    "vless://a96f18f0-4a56-4c4f-be6e-434835f5523c@84.201.169.59:443?security=reality&encryption=none&pbk=e6QVzqAw4kvQHxdu2pFsLnadziIWm9DjOo2rul_NgAk&type=tcp&flow=xtls-rprx-vision&sni=ads.x5.ru&fp=chrome&sid=8ac77e6b777376f8#Russia",
    "vless://09b81314-7592-4ffb-9773-6351de8a7f74@89.208.228.76:7443?encryption=none&type=grpc&security=reality&mode=gun&serviceName=UpdateService&fp=qq&sni=ads.x5.ru&pbk=8hdXyv-YBQIaA2xgOfT2nhfna5y5s19qbZD-SpMZ6hg&sid=dd700a46e27751d1#Russia",
    "vless://09b81314-7592-4ffb-9773-6351de8a7f74@95.163.210.129:7443?encryption=none&type=grpc&security=reality&mode=gun&serviceName=UpdateService&fp=qq&sni=ads.x5.ru&pbk=8hdXyv-YBQIaA2xgOfT2nhfna5y5s19qbZD-SpMZ6hg&sid=dd700a46e27751d1#Russia",
    "vless://db230947-ac07-462a-adeb-b0c7ec994cf5@89.208.228.76:8443?encryption=none&type=grpc&security=reality&mode=gun&serviceName=UpdateService&fp=chrome&sni=sso.passport.yandex.ru&pbk=oWi1Dm7iMdTGeh-BI8rwKcnIaqeG2zF874NrSpPEPlI&sid=77cf23bd7f73c97a#Russia",
    "vless://f5a09282-be6f-48b1-b66c-22dc9d04dc08@158.160.233.48:443?type=grpc&security=reality&encryption=none&fp=chrome&pbk=9lryIkDCyHLzVsVJiGE4LFMuOHdzYDSTNJOFqGlpcl8&sid=2901df419dc4e3ff&sni=static-mon.yandex.net#Russia",
    "vless://1a9e0cbf-7ff3-4b80-87f5-cc53fef2924f@79.137.175.228:8443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=random&sni=rbc.ru&pbk=7zd9mJilgjOrg_ohtw23Vmio-pdnYqeP_r-kiWt87Cg&sid=f4b4a6365558ea2e#Hungary",
    "vless://038f1789-865c-4879-a439-02a6971fb894@146.185.240.172:8443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=random&sni=rbc.ru&pbk=8qHRGcCezzSu4S-Cz9l19BNRLWm4MkaSwZV3dNrLEwc&sid=d515d6cfdfe60b02#Switzerland",
    "vless://19988077-9faf-40d9-ad32-8c4d314aabc9@146.185.240.172:8443?flow=xtls-rprx-vision&encryption=none&type=tcp&security=reality&fp=random&sni=rbc.ru&pbk=8qHRGcCezzSu4S-Cz9l19BNRLWm4MkaSwZV3dNrLEwc&sid=d515d6cfdfe60b02#Switzerland",
    "vless://66b7b555-1854-4071-a3bc-d8fc1ecf47fc@146.185.240.172:8443?type=tcp&security=reality&encryption=none&flow=xtls-rprx-vision&fp=random&pbk=8qHRGcCezzSu4S-Cz9l19BNRLWm4MkaSwZV3dNrLEwc&sid=445ab326fc7c90ac&sni=rbc.ru#Switzerland",
    "vless://418ad4b9-d8be-447c-953d-e666fb154685@217.16.28.63:443?encryption=none&type=grpc&security=reality&mode=gun&serviceName=UpdateService&fp=chrome&sni=eh.vk.com&pbk=_oEGDYSSHrqmbHEUoHbp6YnmNTcXTVdWXcDmpi3JdH0&sid=aefbcf7fc283bd55#Russia",
    "vless://3d142a41-8e57-47d7-a579-f52c6eae79f7@199.232.79.229:80?mode=auto&path=/-AzV2ry?ed=2056&security=none&encryption=none&host=qbank.ir&type=xhttp#US",
    "vless://f829b550-6215-43ad-b8af-ad0cf9eff238@91.107.154.33:443?type=xhttp&encryption=none&path=/&host=&mode=auto&security=reality&pbk=FJb2lztjorICm0c4cJT4jUafnMSBQIjP7-nZr9DDoD0&fp=chrome&sni=stackoverflow.com&spx=/#DE",
    "vless://e7be1334-6a1d-47c0-8c9a-c7a5b8575499@147.182.183.207:443?mode=auto&path=/@Grizzlyvpn&security=reality&encryption=none&pbk=z--KbBlQtkBgTcrtdBJeGeCymIrLdaUDwkb44pAp6nY&fp=chrome&spx=/&type=xhttp&sni=yahoo.com&sid=4c#US",
    "vless://026f3289-2fca-11f1-8c84-dcb6e8e27879@pl5.zoomersky.online:443?encryption=none&mode=auto&path=/&pbk=8HQFveqeGbXX5h_63W0_uZMfyKzY3VlFRVOtuWhX_Hw&security=reality&sni=yahoo.com&type=xhttp#PL",
    "vless://026f3289-2fca-11f1-8c84-dcb6e8e27879@us3.zoomersky.online:443?encryption=none&mode=auto&path=/&pbk=gJpm68zs-qkhnEyj1DNog0ulAb45nyGGgnoIWxMijCY&security=reality&sni=yahoo.com&type=xhttp#US",
    "hysteria2://dongtaiwang.com@62.210.124.146:22000/?insecure=1&sni=www.microsoft.com#FR",
    "hysteria2://ae845cbd-08fb-4346-929a-e28a6f3960a8@sg1.shiyuandian.shop:2056?insecure=1&sni=sg1.shiyuandian.shop#SG",
    "hysteria2://2c833c5d-cbcc-4afb-89ba-d17dc39db6f0@75.127.13.83:47974?insecure=1&sni=www.bing.com#US",
    "vless://4371ad14-b981-4699-bedf-83fb79bde3e6@176.108.242.76:443?security=reality&encryption=none&pbk=FkmYFobwxLMLEktYXywmjthuEYCZggITsxwPNasTKUg&headerType=none&fp=chrome&type=tcp&flow=xtls-rprx-vision&sni=www.vkvideo.ru&sid=6354585c37827955#RU",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 3: COUNTRY FLAGS (ISO 3166-1 alpha-2 -> emoji)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

COUNTRY_FLAGS = {
    "AD": "\U0001f1e6\U0001f1e9", "AE": "\U0001f1e6\U0001f1ea", "AF": "\U0001f1e6\U0001f1eb",
    "AG": "\U0001f1e6\U0001f1ec", "AI": "\U0001f1e6\U0001f1ee", "AL": "\U0001f1e6\U0001f1f1",
    "AM": "\U0001f1e6\U0001f1f2", "AO": "\U0001f1e6\U0001f1f4", "AQ": "\U0001f1e6\U0001f1f6",
    "AR": "\U0001f1e6\U0001f1f7", "AS": "\U0001f1e6\U0001f1f8", "AT": "\U0001f1e6\U0001f1f9",
    "AU": "\U0001f1e6\U0001f1fa", "AW": "\U0001f1e6\U0001f1fc", "AX": "\U0001f1e6\U0001f1fd",
    "AZ": "\U0001f1e6\U0001f1ff", "BA": "\U0001f1e7\U0001f1e6", "BB": "\U0001f1e7\U0001f1e7",
    "BD": "\U0001f1e7\U0001f1e9", "BE": "\U0001f1e7\U0001f1ea", "BF": "\U0001f1e7\U0001f1eb",
    "BG": "\U0001f1e7\U0001f1ec", "BH": "\U0001f1e7\U0001f1ed", "BI": "\U0001f1e7\U0001f1ee",
    "BJ": "\U0001f1e7\U0001f1ef", "BL": "\U0001f1e7\U0001f1f1", "BM": "\U0001f1e7\U0001f1f2",
    "BN": "\U0001f1e7\U0001f1f3", "BO": "\U0001f1e7\U0001f1f4", "BR": "\U0001f1e7\U0001f1f7",
    "BS": "\U0001f1e7\U0001f1f8", "BT": "\U0001f1e7\U0001f1f9", "BV": "\U0001f1e7\U0001f1fb",
    "BW": "\U0001f1e7\U0001f1fc", "BY": "\U0001f1e7\U0001f1fe", "BZ": "\U0001f1e7\U0001f1ff",
    "CA": "\U0001f1e8\U0001f1e6", "CC": "\U0001f1e8\U0001f1e8", "CD": "\U0001f1e8\U0001f1e9",
    "CF": "\U0001f1e8\U0001f1eb", "CG": "\U0001f1e8\U0001f1ec", "CH": "\U0001f1e8\U0001f1ed",
    "CI": "\U0001f1e8\U0001f1ee", "CK": "\U0001f1e8\U0001f1f0", "CL": "\U0001f1e8\U0001f1f1",
    "CM": "\U0001f1e8\U0001f1f2", "CN": "\U0001f1e8\U0001f1f3", "CO": "\U0001f1e8\U0001f1f4",
    "CR": "\U0001f1e8\U0001f1f7", "CU": "\U0001f1e8\U0001f1fa", "CV": "\U0001f1e8\U0001f1fb",
    "CW": "\U0001f1e8\U0001f1fc", "CX": "\U0001f1e8\U0001f1fd", "CY": "\U0001f1e8\U0001f1fe",
    "CZ": "\U0001f1e8\U0001f1ff", "DE": "\U0001f1e9\U0001f1ea", "DJ": "\U0001f1e9\U0001f1ef",
    "DK": "\U0001f1e9\U0001f1f0", "DM": "\U0001f1e9\U0001f1f2", "DO": "\U0001f1e9\U0001f1f4",
    "DZ": "\U0001f1e9\U0001f1ff", "EC": "\U0001f1ea\U0001f1e8", "EE": "\U0001f1ea\U0001f1ea",
    "EG": "\U0001f1ea\U0001f1ec", "EH": "\U0001f1ea\U0001f1ed", "ER": "\U0001f1ea\U0001f1f7",
    "ES": "\U0001f1ea\U0001f1f8", "ET": "\U0001f1ea\U0001f1f9", "FI": "\U0001f1eb\U0001f1ee",
    "FJ": "\U0001f1eb\U0001f1ef", "FK": "\U0001f1eb\U0001f1f0", "FM": "\U0001f1eb\U0001f1f2",
    "FO": "\U0001f1eb\U0001f1f4", "FR": "\U0001f1eb\U0001f1f7", "GA": "\U0001f1ec\U0001f1e6",
    "GB": "\U0001f1ec\U0001f1e7", "GD": "\U0001f1ec\U0001f1e9", "GE": "\U0001f1ec\U0001f1ea",
    "GF": "\U0001f1ec\U0001f1eb", "GG": "\U0001f1ec\U0001f1ec", "GH": "\U0001f1ec\U0001f1ed",
    "GI": "\U0001f1ec\U0001f1ee", "GL": "\U0001f1ec\U0001f1f1", "GM": "\U0001f1ec\U0001f1f2",
    "GN": "\U0001f1ec\U0001f1f3", "GP": "\U0001f1ec\U0001f1f5", "GQ": "\U0001f1ec\U0001f1f6",
    "GR": "\U0001f1ec\U0001f1f7", "GS": "\U0001f1ec\U0001f1f8", "GT": "\U0001f1ec\U0001f1f9",
    "GU": "\U0001f1ec\U0001f1fa", "GW": "\U0001f1ec\U0001f1fc", "GY": "\U0001f1ec\U0001f1fe",
    "HK": "\U0001f1ed\U0001f1f0", "HM": "\U0001f1ed\U0001f1f2", "HN": "\U0001f1ed\U0001f1f3",
    "HR": "\U0001f1ed\U0001f1f7", "HT": "\U0001f1ed\U0001f1f9", "HU": "\U0001f1ed\U0001f1fa",
    "ID": "\U0001f1ee\U0001f1e9", "IE": "\U0001f1ee\U0001f1ea", "IL": "\U0001f1ee\U0001f1f1",
    "IM": "\U0001f1ee\U0001f1f2", "IN": "\U0001f1ee\U0001f1f3", "IO": "\U0001f1ee\U0001f1f4",
    "IQ": "\U0001f1ee\U0001f1f6", "IR": "\U0001f1ee\U0001f1f7", "IS": "\U0001f1ee\U0001f1f8",
    "IT": "\U0001f1ee\U0001f1f9", "JE": "\U0001f1ef\U0001f1ea", "JM": "\U0001f1ef\U0001f1f2",
    "JO": "\U0001f1ef\U0001f1f4", "JP": "\U0001f1ef\U0001f1f5", "KE": "\U0001f1f0\U0001f1ea",
    "KG": "\U0001f1f0\U0001f1ec", "KH": "\U0001f1f0\U0001f1ed", "KI": "\U0001f1f0\U0001f1ee",
    "KM": "\U0001f1f0\U0001f1f2", "KN": "\U0001f1f0\U0001f1f3", "KP": "\U0001f1f0\U0001f1f5",
    "KR": "\U0001f1f0\U0001f1f7", "KW": "\U0001f1f0\U0001f1fc", "KY": "\U0001f1f0\U0001f1fe",
    "KZ": "\U0001f1f0\U0001f1ff", "LA": "\U0001f1f1\U0001f1e6", "LB": "\U0001f1f1\U0001f1e7",
    "LC": "\U0001f1f1\U0001f1e8", "LI": "\U0001f1f1\U0001f1ee", "LK": "\U0001f1f1\U0001f1f0",
    "LR": "\U0001f1f1\U0001f1f7", "LS": "\U0001f1f1\U0001f1f8", "LT": "\U0001f1f1\U0001f1f9",
    "LU": "\U0001f1f1\U0001f1fa", "LV": "\U0001f1f1\U0001f1fb", "LY": "\U0001f1f1\U0001f1fe",
    "MA": "\U0001f1f2\U0001f1e6", "MC": "\U0001f1f2\U0001f1e8", "MD": "\U0001f1f2\U0001f1e9",
    "ME": "\U0001f1f2\U0001f1ea", "MF": "\U0001f1f2\U0001f1eb", "MG": "\U0001f1f2\U0001f1ec",
    "MH": "\U0001f1f2\U0001f1ed", "MK": "\U0001f1f2\U0001f1f0", "ML": "\U0001f1f2\U0001f1f1",
    "MM": "\U0001f1f2\U0001f1f2", "MN": "\U0001f1f2\U0001f1f3", "MO": "\U0001f1f2\U0001f1f4",
    "MP": "\U0001f1f2\U0001f1f5", "MQ": "\U0001f1f2\U0001f1f6", "MR": "\U0001f1f2\U0001f1f7",
    "MS": "\U0001f1f2\U0001f1f8", "MT": "\U0001f1f2\U0001f1f9", "MU": "\U0001f1f2\U0001f1fa",
    "MV": "\U0001f1f2\U0001f1fb", "MW": "\U0001f1f2\U0001f1fc", "MX": "\U0001f1f2\U0001f1fd",
    "MY": "\U0001f1f2\U0001f1fe", "MZ": "\U0001f1f2\U0001f1ff", "NA": "\U0001f1f3\U0001f1e6",
    "NC": "\U0001f1f3\U0001f1e8", "NE": "\U0001f1f3\U0001f1ea", "NF": "\U0001f1f3\U0001f1eb",
    "NG": "\U0001f1f3\U0001f1ec", "NI": "\U0001f1f3\U0001f1ee", "NL": "\U0001f1f3\U0001f1f1",
    "NO": "\U0001f1f3\U0001f1f4", "NP": "\U0001f1f3\U0001f1f5", "NR": "\U0001f1f3\U0001f1f6",
    "NU": "\U0001f1f3\U0001f1fa", "NZ": "\U0001f1f3\U0001f1ff", "OM": "\U0001f1f4\U0001f1f2",
    "PA": "\U0001f1f5\U0001f1e6", "PE": "\U0001f1f5\U0001f1ea", "PF": "\U0001f1f5\U0001f1eb",
    "PG": "\U0001f1f5\U0001f1ec", "PH": "\U0001f1f5\U0001f1ed", "PK": "\U0001f1f5\U0001f1f0",
    "PL": "\U0001f1f5\U0001f1f1", "PM": "\U0001f1f5\U0001f1f2", "PN": "\U0001f1f5\U0001f1f3",
    "PR": "\U0001f1f5\U0001f1f7", "PS": "\U0001f1f5\U0001f1f8", "PT": "\U0001f1f5\U0001f1f9",
    "PW": "\U0001f1f5\U0001f1fc", "PY": "\U0001f1f5\U0001f1fe", "QA": "\U0001f1f6\U0001f1e6",
    "RE": "\U0001f1f7\U0001f1ea", "RO": "\U0001f1f7\U0001f1f4", "RS": "\U0001f1f7\U0001f1f8",
    "RU": "\U0001f1f7\U0001f1fa", "RW": "\U0001f1f7\U0001f1fc", "SA": "\U0001f1f8\U0001f1e6",
    "SB": "\U0001f1f8\U0001f1e7", "SC": "\U0001f1f8\U0001f1e8", "SD": "\U0001f1f8\U0001f1e9",
    "SE": "\U0001f1f8\U0001f1ea", "SG": "\U0001f1f8\U0001f1ec", "SH": "\U0001f1f8\U0001f1ed",
    "SI": "\U0001f1f8\U0001f1ee", "SJ": "\U0001f1f8\U0001f1ef", "SK": "\U0001f1f8\U0001f1f0",
    "SL": "\U0001f1f8\U0001f1f1", "SM": "\U0001f1f8\U0001f1f2", "SN": "\U0001f1f8\U0001f1f3",
    "SO": "\U0001f1f8\U0001f1f4", "SR": "\U0001f1f8\U0001f1f7", "SS": "\U0001f1f8\U0001f1f8",
    "ST": "\U0001f1f8\U0001f1f9", "SV": "\U0001f1f8\U0001f1fb", "SX": "\U0001f1f8\U0001f1fd",
    "SY": "\U0001f1f8\U0001f1fe", "SZ": "\U0001f1f8\U0001f1ff", "TC": "\U0001f1f9\U0001f1e8",
    "TD": "\U0001f1f9\U0001f1e9", "TF": "\U0001f1f9\U0001f1eb", "TG": "\U0001f1f9\U0001f1ec",
    "TH": "\U0001f1f9\U0001f1ed", "TJ": "\U0001f1f9\U0001f1ef", "TK": "\U0001f1f9\U0001f1f0",
    "TL": "\U0001f1f9\U0001f1f1", "TM": "\U0001f1f9\U0001f1f2", "TN": "\U0001f1f9\U0001f1f3",
    "TO": "\U0001f1f9\U0001f1f4", "TR": "\U0001f1f9\U0001f1f7", "TT": "\U0001f1f9\U0001f1f9",
    "TV": "\U0001f1f9\U0001f1fb", "TW": "\U0001f1f9\U0001f1fc", "TZ": "\U0001f1f9\U0001f1ff",
    "UA": "\U0001f1fa\U0001f1e6", "UG": "\U0001f1fa\U0001f1ec", "UM": "\U0001f1fa\U0001f1f2",
    "US": "\U0001f1fa\U0001f1f8", "UY": "\U0001f1fa\U0001f1fe", "UZ": "\U0001f1fa\U0001f1ff",
    "VA": "\U0001f1fb\U0001f1e6", "VC": "\U0001f1fb\U0001f1e8", "VE": "\U0001f1fb\U0001f1ea",
    "VG": "\U0001f1fb\U0001f1ec", "VI": "\U0001f1fb\U0001f1ee", "VN": "\U0001f1fb\U0001f1f3",
    "VU": "\U0001f1fb\U0001f1fa", "WF": "\U0001f1fc\U0001f1eb", "WS": "\U0001f1fc\U0001f1f8",
    "XK": "\U0001f1fd\U0001f1f0", "YE": "\U0001f1fe\U0001f1ea", "YT": "\U0001f1fe\U0001f1f9",
    "ZA": "\U0001f1ff\U0001f1e6", "ZM": "\U0001f1ff\U0001f1f2", "ZW": "\U0001f1ff\U0001f1ff",
    "Anycast": "\U0001f310", "Other": "\U0001f30d", "Unknown": "\u2753",
}

COUNTRY_NAME_TO_CODE = {
    "Austria": "AT", "Australia": "AU", "Azerbaijan": "AZ",
    "Belgium": "BE", "Brazil": "BR", "Bulgaria": "BG", "Canada": "CA",
    "Switzerland": "CH", "Czech": "CZ", "Czechia": "CZ",
    "Germany": "DE", "Denmark": "DK", "Spain": "ES", "Finland": "FI",
    "France": "FR", "United Kingdom": "GB", "UK": "GB", "Hong Kong": "HK",
    "Croatia": "HR", "Hungary": "HU", "Indonesia": "ID", "Ireland": "IE",
    "Israel": "IL", "India": "IN", "Italy": "IT", "Japan": "JP",
    "Kazakhstan": "KZ", "Lithuania": "LT", "Latvia": "LV", "Moldova": "MD",
    "The Netherlands": "NL", "Netherlands": "NL", "Norway": "NO",
    "Philippines": "PH", "Poland": "PL", "Portugal": "PT", "Romania": "RO",
    "Russia": "RU", "Sweden": "SE", "Singapore": "SG", "Slovakia": "SK",
    "Turkey": "TR", "Ukraine": "UA", "United States": "US", "USA": "US",
    "Uzbekistan": "UZ", "South Africa": "ZA", "Iran": "IR",
    "United Arab Emirates": "AE", "UAE": "AE", "Turkey": "TR",
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 4: UI — Colors, logging, progress bar, table printer
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class C:
    """ANSI color codes for terminal output."""
    R = "\033[0m"
    B = "\033[1m"
    RED = "\033[91m"
    GRN = "\033[92m"
    YEL = "\033[93m"
    BLU = "\033[94m"
    MAG = "\033[95m"
    CYN = "\033[96m"
    WHT = "\033[97m"
    DIM = "\033[2m"
    GRAY = "\033[90m"


# Global state with thread lock
_state = {
    "lock": threading.Lock(),
    "sources_tried": 0,
    "sources_ok": 0,
    "configs_found": 0,
    "ping_done": 0,
    "ping_total": 0,
    "ping_alive": 0,
    "ping_dead": 0,
}

# DNS resolution cache: hostname -> (ip, timestamp)
_dns_cache = {}
_dns_cache_lock = threading.Lock()
DNS_CACHE_TTL = 300  # 5 minutes

# Source reliability tracking: source_name -> {tried, ok, alive, total_configs}
_source_stats = {}
_source_stats_lock = threading.Lock()

# Duplicate detection: proto:host:port -> [source_names]
_config_sources = {}
_config_sources_lock = threading.Lock()

_interrupted = False
_verbose = False
_quiet = False


def _sig_handler(sig_num, frame):
    """Handle Ctrl+C gracefully."""
    global _interrupted
    _interrupted = True
    print(f"\n\n  {C.YEL}\u26a0  Прервано. Сохраняю результаты...{C.R}")


signal.signal(signal.SIGINT, _sig_handler)


def banner():
    """Print the script banner."""
    print(f"""
{C.CYN}\u2554{'=' * 69}\u2557
\u2551  {C.B}\u26a1 PROXY FORGE v9.0{C.R}{C.CYN}  \u2014  ULTIMATE EDITION                     \u2551
\u2551  {C.YEL}CDN Mirrors | TG Scanner | DPI Score | Clash | JSON | 100+ Sources{C.R}  \u2551
\u2551  {C.DIM}VLESS Reality/XHTTP | VMess | Trojan | SS | HY2 | TUIC | WG{C.R}       \u2551
\u2550{'=' * 69}\u2550{C.R}
""")


def info(msg):
    """Print info message."""
    if not _quiet:
        print(f"  {C.BLU}\u2139{C.R}  {msg}")


def ok(msg):
    """Print success message."""
    if not _quiet:
        print(f"  {C.GRN}\u2713{C.R}  {msg}")


def warn(msg):
    """Print warning message."""
    if not _quiet:
        print(f"  {C.YEL}\u26a0{C.R}  {msg}")


def err(msg):
    """Print error message."""
    if not _quiet:
        print(f"  {C.RED}\u2717{C.R}  {msg}")


def verbose(msg):
    """Print verbose message (only in verbose mode)."""
    if _verbose and not _quiet:
        print(f"  {C.DIM}\u251c {msg}{C.R}")


def head(msg):
    """Print section header."""
    if not _quiet:
        print(f"\n  {C.B}{C.CYN}\u2500\u2500 {msg} \u2500\u2500{C.R}")


def prog(cur, tot, width=35, prefix=""):
    """Print/update progress bar on same line."""
    if _quiet:
        return
    if tot <= 0:
        return
    ratio = cur / tot
    filled = int(width * ratio)
    empty = width - filled
    bar = "\u2588" * filled + "\u2591" * empty
    pct = int(ratio * 100)
    sys.stdout.write(
        f"\r  {C.CYN}\u27f3{C.R}  {prefix}[{bar}] {pct}% ({cur}/{tot})"
    )
    sys.stdout.flush()
    if cur >= tot:
        print()


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 5: NETWORK — Download, CDN mirrors, TCP ping, DNS cache
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def dl_text(url, timeout=DL_TIMEOUT):
    """
    Базовая загрузка текста по URL.
    Пропускает HTML-страницы с ошибками. SSL без верификации.
    Возвращает декодированный текст или None.
    """
    try:
        req = Request(url, headers=HTTP_HEADERS)
        resp = urlopen(req, timeout=timeout, context=_ssl_ctx)
        raw = resp.read()
        # Проверяем Content-Type для определения кодировки
        content_type = resp.headers.get("Content-Type", "")
        if "utf-8" in content_type.lower():
            text = raw.decode("utf-8")
        else:
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                text = raw.decode("latin-1")
        # Пропускаем HTML-страницы с ошибками (404, 503, etc.)
        if text.strip().startswith("<!DOCTYPE") or text.strip().startswith("<html"):
            return None
        return text
    except Exception:
        return None


def _generate_cdn_mirrors(url):
    """
    Генерирует CDN-зеркала для GitHub URL.
    Порядок: jsDelivr -> ghfast.top -> gh-proxy.com -> ghps.cc ->
             mirror.ghproxy.com -> gh.api.99988866.xyz -> оригинал.
    Для не-GitHub URL возвращает только оригинал.
    """
    mirrors = []

    # raw.githubusercontent.com/USER/REPO/BRANCH/path
    m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)", url)
    if m:
        user, repo, branch, path = m.groups()
        raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"
        mirrors.append(f"https://cdn.jsdelivr.net/gh/{user}/{repo}@{branch}/{path}")
        mirrors.append(f"https://ghfast.top/{raw_url}")
        mirrors.append(f"https://gh-proxy.com/{raw_url}")
        mirrors.append(f"https://ghps.cc/{raw_url}")
        mirrors.append(f"https://mirror.ghproxy.com/{raw_url}")
        mirrors.append(f"https://gh.api.99988866.xyz/{raw_url}")
        mirrors.append(url)
        return mirrors

    # github.com/USER/REPO/raw/BRANCH/path
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/raw/([^/]+)/(.+)", url)
    if m:
        user, repo, branch, path = m.groups()
        raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"
        mirrors.append(f"https://cdn.jsdelivr.net/gh/{user}/{repo}@{branch}/{path}")
        mirrors.append(f"https://ghfast.top/{raw_url}")
        mirrors.append(f"https://gh-proxy.com/{raw_url}")
        mirrors.append(f"https://ghps.cc/{raw_url}")
        mirrors.append(url)
        return mirrors

    # github.com/USER/REPO/blob/BRANCH/path
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", url)
    if m:
        user, repo, branch, path = m.groups()
        raw_url = f"https://raw.githubusercontent.com/{user}/{repo}/{branch}/{path}"
        mirrors.append(f"https://cdn.jsdelivr.net/gh/{user}/{repo}@{branch}/{path}")
        mirrors.append(f"https://ghfast.top/{raw_url}")
        mirrors.append(f"https://gh-proxy.com/{raw_url}")
        mirrors.append(f"https://ghps.cc/{raw_url}")
        mirrors.append(url)
        return mirrors

    mirrors.append(url)
    return mirrors


def dl_with_mirrors(url, timeout=DL_TIMEOUT):
    """
    Загрузка с CDN-зеркалами по цепочке fallback.
    Пробует каждое зеркало по порядку, пока одно не сработает.
    Возвращает декодированный текст или None.
    """
    if _interrupted:
        return None

    # Если URL уже на CDN, пробуем его сначала
    if "cdn.jsdelivr.net" in url:
        text = dl_text(url, timeout)
        if text and len(text) > 20:
            return text
        # Пробуем конвертировать в raw GitHub URL
        jsd_pattern = r"https://cdn\.jsdelivr\.net/gh/([^@]+)@([^/]+)/(.+)"
        m = re.match(jsd_pattern, url)
        if m:
            user_repo = m.group(1)
            branch = m.group(2)
            path = m.group(3)
            direct = f"https://raw.githubusercontent.com/{user_repo}/{branch}/{path}"
            mirrors = _generate_cdn_mirrors(direct)
            for mirror in mirrors:
                if mirror == url:
                    continue
                if _interrupted:
                    return None
                text = dl_text(mirror, timeout)
                if text and len(text) > 20:
                    return text
        return None

    # Для GitHub raw URL генерируем CDN-зеркала
    mirrors = _generate_cdn_mirrors(url)
    for mirror in mirrors:
        if _interrupted:
            return None
        text = dl_text(mirror, timeout)
        if text and len(text) > 20:
            return text
    return None


def _dns_resolve_cached(hostname):
    """
    Разрешает DNS-имя с кэшированием результата.
    Возвращает IP-адрес (str) или None.
    """
    global _dns_cache
    if not hostname:
        return None
    # Проверяем IPv6
    if hostname.startswith("[") and "]" in hostname:
        return hostname.strip("[]")

    now = time.time()
    with _dns_cache_lock:
        if hostname in _dns_cache:
            ip, ts = _dns_cache[hostname]
            if now - ts < DNS_CACHE_TTL:
                return ip
    try:
        addrinfo = socket.getaddrinfo(hostname, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        if addrinfo:
            ip = addrinfo[0][4][0]
            with _dns_cache_lock:
                _dns_cache[hostname] = (ip, now)
            return ip
    except Exception:
        pass
    return None


def tcp_ping(host, port, timeout=PING_TIMEOUT):
    """
    TCP connect timing. Возвращает задержку в мс или -1 при ошибке.
    Поддерживает IPv6.
    """
    try:
        port = int(port)
    except (ValueError, TypeError):
        return -1
    try:
        # Определяем семейство адресов (IPv4 или IPv6)
        if ":" in host and not (host.startswith("[") and host.endswith("]")):
            # IPv6 без скобок
            af = socket.AF_INET6
            addr = (host, port, 0, 0)
        elif host.startswith("["):
            # IPv6 в скобках [::1]:port
            h = host.strip("[]")
            af = socket.AF_INET6
            addr = (h, port, 0, 0)
        else:
            af = socket.AF_INET
            addr = (host, port)
        sock = socket.socket(af, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        start = time.time()
        sock.connect(addr)
        elapsed = (time.time() - start) * 1000
        sock.close()
        return round(elapsed, 1)
    except Exception:
        return -1


def tcp_ping_avg(host, port, timeout=PING_TIMEOUT, count=1):
    """
    Средняя задержка TCP ping по нескольким попыткам.
    count=1 — одна попытка (как раньше).
    Возвращает среднюю задержку в мс или -1.
    """
    if count <= 1:
        return tcp_ping(host, port, timeout)
    results = []
    for _ in range(count):
        if _interrupted:
            break
        ms = tcp_ping(host, port, timeout)
        if ms > 0:
            results.append(ms)
    if not results:
        return -1
    return round(sum(results) / len(results), 1)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 6: PARSING — Config extraction, host/port, country, DPI, metadata
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _get_proto(link):
    """Extract protocol name from config URI."""
    link_lower = link.lower()
    for prefix, name in PROTO_NAMES.items():
        if link_lower.startswith(prefix):
            return name
    return "UNKNOWN"


def _get_host_port(link):
    """
    Extract host and port from config URI.
    Handles: vless://uuid@host:port, vmess://base64, ss://method:pass@host:port,
             hysteria2://pass@host:port, trojan://pass@host:port, IPv6, etc.
    """
    try:
        no_frag = link.split("#")[0]
        # Для vmess:// декодируем base64 JSON
        if no_frag.lower().startswith("vmess://"):
            b64_part = no_frag[8:]
            b64_clean = re.sub(r'[^A-Za-z0-9+/=]', '', b64_part)
            padding = 4 - len(b64_clean) % 4
            if padding != 4:
                b64_clean += "=" * padding
            try:
                decoded = base64.b64decode(b64_clean).decode("utf-8")
                data = json.loads(decoded)
                host = data.get("add", "")
                port = data.get("port", "")
                if host and port:
                    return host, str(port)
            except Exception:
                pass
            return None, None

        # Убираем префикс протокола
        for prefix in SUPPORTED_PROTOCOLS:
            if no_frag.lower().startswith(prefix):
                no_frag = no_frag[len(prefix):]
                break

        # Убираем query string
        no_frag = no_frag.split("?")[0]

        # Ищем паттерн host:port
        at_match = re.match(r'^[^@]+@(.+)$', no_frag)
        if at_match:
            addr = at_match.group(1)
        else:
            addr = no_frag

        # IPv6 [::1]:port
        ipv6_match = re.match(r'^\[(.+)\]:(\d+)$', addr)
        if ipv6_match:
            return ipv6_match.group(1), ipv6_match.group(2)

        # host:port
        hp_match = re.match(r'^([^:]+):(\d+)$', addr)
        if hp_match:
            return hp_match.group(1), hp_match.group(2)

        # host без порта (некоторые hysteria2)
        if re.match(r'^[a-zA-Z0-9._-]+$', addr):
            return addr, None

        return None, None
    except Exception:
        return None, None


def _get_country(link):
    """Extract country from fragment (#Country or #emoji Country ...)."""
    try:
        frag = unquote(link.split("#")[-1]) if "#" in link else ""
        frag = frag.strip()
        cleaned = re.sub(r'[\U0001f1e0-\U0001f1ff]+', '', frag)
        cleaned = re.sub(r'\[.*?\]', '', cleaned)
        cleaned = cleaned.replace('*', '').strip()
        cleaned = re.sub(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', '', cleaned)
        cleaned = re.sub(r'\|.*$', '', cleaned).strip()
        parts = cleaned.split()
        if parts:
            country = parts[0].strip()
            if len(country) <= 20 and re.match(r'^[A-Za-z]+$', country):
                return country
            frag_clean = re.sub(r'\[.*?\]', '', frag).strip()
            frag_clean = re.sub(r'[\U0001f1e0-\U0001f1ff]+', '', frag_clean).strip()
            frag_clean = re.sub(r'\|.*$', '', frag_clean).strip()
            frag_clean = frag_clean.rstrip('0123456789').strip()
            if len(frag_clean) <= 25:
                return frag_clean[:20] if frag_clean else "??"
        return "??"
    except Exception:
        return "??"


def _get_country_code(country_name):
    """Convert country name to ISO code."""
    if not country_name or country_name == "??":
        return "Unknown"
    if country_name in COUNTRY_NAME_TO_CODE:
        return COUNTRY_NAME_TO_CODE[country_name]
    for key, code in COUNTRY_NAME_TO_CODE.items():
        if key.lower() in country_name.lower() or country_name.lower() in key.lower():
            return code
    # Попробуем первые 2 буквы как код
    if len(country_name) >= 2 and country_name[:2].upper() in COUNTRY_FLAGS:
        return country_name[:2].upper()
    return "Unknown"


def _get_name(link):
    """Extract display name from fragment."""
    try:
        if "#" in link:
            return unquote(link.split("#")[-1]).strip()
        return _get_proto(link)
    except Exception:
        return "??"


def _get_transport(link):
    """Extract transport type from config parameters."""
    try:
        frag = link.split("?")[1] if "?" in link else ""
        params = parse_qs(frag)
        net = params.get("type", [""])[0].lower()
        security = params.get("security", [""])[0].lower()
        mode = params.get("mode", [""])[0].lower()

        if net == "xhttp" or mode == "auto":
            if security == "reality":
                return "xhttp+reality"
            elif security == "tls":
                return "xhttp+tls"
            else:
                return "xhttp"
        elif net == "ws":
            if security == "reality":
                return "ws+reality"
            elif security == "tls":
                return "ws+tls"
            else:
                return "ws"
        elif net == "grpc":
            if security == "reality":
                return "grpc+reality"
            elif security == "tls":
                return "grpc+tls"
            else:
                return "grpc"
        elif net == "tcp":
            if security == "reality":
                return "tcp+reality"
            elif security == "tls":
                return "tcp+tls"
            else:
                return "tcp"
        elif net == "h2" or net == "http":
            if security == "reality":
                return "h2+reality"
            elif security == "tls":
                return "h2+tls"
            else:
                return "h2"
        elif net == "kcp":
            return "kcp"
        elif net == "quic":
            return "quic"

        proto = _get_proto(link)
        if proto == "HYSTERIA2":
            return "quic"
        elif proto == "TROJAN":
            return "tcp+tls"
        elif proto == "TUIC":
            return "quic"
        elif proto == "WIREGUARD":
            return "udp"

        return "tcp"
    except Exception:
        return "tcp"


def _get_security(link):
    """Extract security type from config parameters."""
    try:
        frag = link.split("?")[1] if "?" in link else ""
        params = parse_qs(frag)
        return params.get("security", ["none"])[0].upper()
    except Exception:
        return "NONE"


def _dpi_score(link):
    """
    DPI resistance scoring (0-100).
    Higher score = more resistant to DPI detection.
    ENHANCED: +3 for packetEncoding=xudp, +3 for alpn=h2, +3 for spx path,
              +3 for serviceName in gRPC.
    """
    try:
        score = 0
        frag = link.split("?")[1] if "?" in link else ""
        params = parse_qs(frag)
        proto = _get_proto(link)
        net = params.get("type", [""])[0].lower()
        security = params.get("security", [""])[0].lower()
        flow = params.get("flow", [""])[0].lower()
        sni = params.get("sni", [""])[0].lower()
        fp = params.get("fp", [""])[0].lower()
        alpn = params.get("alpn", [""])[0].lower()
        packet_encoding = params.get("packetEncoding", [""])[0].lower()
        spx = params.get("spx", [""])[0].lower()
        service_name = params.get("serviceName", [""])[0].lower()
        host_port = _get_host_port(link)
        host = host_port[0] if host_port and host_port[0] else ""

        # Protocol scoring
        if proto == "VLESS":
            score += 15
        elif proto == "HYSTERIA2":
            score += 25
        elif proto == "TUIC":
            score += 20
        elif proto == "TROJAN":
            score += 10
        elif proto == "SS":
            score += 8
        elif proto == "WIREGUARD":
            score += 18
        else:
            score += 5

        # Security layer
        if security == "reality":
            score += 30
        elif security == "tls":
            score += 15
        elif security == "none":
            score -= 5

        # Transport type
        if net == "xhttp" or params.get("mode", [""])[0].lower() == "auto":
            score += 15
        elif net == "grpc":
            score += 10
        elif net == "ws":
            score += 5

        # XTLS flow
        if "xtls" in flow or "vision" in flow:
            score += 10

        # Fingerprint
        if fp in ("chrome", "randomized", "random"):
            score += 5
        elif fp == "qq":
            score += 3

        # ENHANCED: packetEncoding=xudp
        if packet_encoding == "xudp":
            score += 3

        # ENHANCED: alpn=h2
        if "h2" in alpn:
            score += 3

        # ENHANCED: spx path
        if spx:
            score += 3

        # ENHANCED: serviceName for gRPC
        if service_name:
            score += 3

        # SNI legitimacy
        if sni in (s.lower() for s in LEGITIMATE_SNI):
            score += 10
        if host:
            for cdn in CDN_HOSTS:
                if cdn in host.lower():
                    score += 10
                    break
            for legit in LEGITIMATE_SNI:
                if legit.lower() == host.lower():
                    score += 8
                    break

        return max(0, min(100, score))
    except Exception:
        return 0


def _validate_config_structure(link):
    """
    Basic config structure validation.
    Returns True if config has valid host, port, and UUID/key.
    """
    try:
        host, port = _get_host_port(link)
        if not host or not port:
            return False
        proto = _get_proto(link)
        # Проверяем UUID для VLESS и VMess
        if proto in ("VLESS",):
            uuid_match = re.search(
                r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}',
                link.lower()
            )
            if not uuid_match:
                return False
        return True
    except Exception:
        return False


def _extract_configs(text):
    """
    Extract config lines from text. Deduplicates by proto:host:port.
    Returns list of unique config URI strings.
    """
    if not text:
        return []
    lines = text.replace("\r\n", "\n").split("\n")
    configs = []
    seen = set()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        matched = False
        for prefix in SUPPORTED_PROTOCOLS:
            if line.lower().startswith(prefix):
                matched = True
                break
        if not matched:
            continue

        host, port = _get_host_port(line)
        proto = _get_proto(line)
        if host and port:
            key = f"{proto}:{host}:{port}"
            if key not in seen:
                seen.add(key)
                configs.append(line)
        else:
            if line not in seen:
                seen.add(line)
                configs.append(line)

    return configs


def parse_subscription(text, source, tags):
    """
    Parse subscription response text. Extracts configs and metadata.
    Returns dict with all metadata fields.
    """
    result = {
        "source": source,
        "tags": tags,
        "configs": [],
        "upload": 0,
        "download": 0,
        "total": 0,
        "expire": 0,
        "sub_type": "unknown",
        "duration": "",
        "header_text": "",
        "traffic_limit": "",
        "test_duration": "",
    }

    if not text:
        return result

    lines = text.replace("\r\n", "\n").split("\n")

    # Extract subscription-userinfo header
    for line in lines[:5]:
        if "subscription-userinfo" in line.lower():
            match = re.search(
                r'upload=(\d+);\s*download=(\d+);\s*total=(\d+);\s*expire=(\d+)',
                line, re.IGNORECASE
            )
            if match:
                result["upload"] = int(match.group(1))
                result["download"] = int(match.group(2))
                result["total"] = int(match.group(3))
                result["expire"] = int(match.group(4))
            break

    # Extract header text
    header_lines = []
    for line in lines[:50]:
        stripped = line.strip()
        if not stripped:
            continue
        is_config = False
        for prefix in SUPPORTED_PROTOCOLS:
            if stripped.lower().startswith(prefix):
                is_config = True
                break
        if is_config:
            continue
        if stripped.lower().startswith("http://") or stripped.lower().startswith("https://"):
            continue
        header_lines.append(stripped)
    result["header_text"] = "\n".join(header_lines)

    ht_lower = result["header_text"].lower()

    # Classify subscription type
    if any(kw in ht_lower for kw in ("free", "free ", "free-", "gratis", "бесплатно")):
        result["sub_type"] = "free"
    elif any(kw in ht_lower for kw in ("trial", "test", "тест", "проб", "демо")):
        result["sub_type"] = "trial"
    elif any(kw in ht_lower for kw in ("expire", "expir", "истек", "просроч")):
        result["sub_type"] = "expired"
    elif result["total"] > 0 or result["expire"] > 0:
        result["sub_type"] = "subscription"

    # Compute human-readable metadata
    if result["total"] > 0:
        total_gb = result["total"] / (1024 ** 3)
        result["traffic_limit"] = f"{total_gb:.1f} GB"
        used_gb = (result["upload"] + result["download"]) / (1024 ** 3)
        result["traffic_limit"] += f" (исп: {used_gb:.2f} GB)"

    if result["expire"] > 0:
        try:
            expire_dt = datetime.fromtimestamp(result["expire"], tz=timezone.utc)
            now = datetime.now(timezone.utc)
            if expire_dt > now:
                delta = expire_dt - now
                days = delta.days
                hours = delta.seconds // 3600
                if days > 365:
                    result["test_duration"] = f"~{days // 365} год(а)"
                elif days > 30:
                    result["test_duration"] = f"~{days // 30} мес ({days} дн)"
                elif days > 0:
                    result["test_duration"] = f"{days} дн {hours} ч"
                else:
                    result["test_duration"] = f"{hours} ч {delta.seconds // 60} мин"
            else:
                result["test_duration"] = "\u26a0 ИСТЁК"
                result["sub_type"] = "expired"
        except Exception:
            pass

    # Advanced traffic pattern matching
    if not result["traffic_limit"]:
        traffic_match = re.search(
            r'(?:traffic|limit|quota|upload|total)[\s:=]+(\d+(?:\.\d+)?)\s*(GB|MB|TB)',
            result["header_text"], re.IGNORECASE
        )
        if not traffic_match:
            traffic_match = re.search(
                r'(\d+(?:\.\d+)?)\s*(GB|MB|TB)\s*(?:/(day|hour|день|час|мес))?',
                result["header_text"], re.IGNORECASE
            )
        if traffic_match:
            val = traffic_match.group(1)
            unit = traffic_match.group(2).upper()
            period = traffic_match.group(3) if len(traffic_match.groups()) > 2 else None
            if period:
                period_map = {"day": "день", "hour": "час", "день": "день", "час": "час", "мес": "мес"}
                result["traffic_limit"] = f"{val} {unit}/{period_map.get(period, period)}"
            else:
                result["traffic_limit"] = f"{val} {unit}"

    # Advanced duration matching
    if not result["test_duration"]:
        duration_match = re.search(
            r'(\d+)\s*(day|hour|min|дн|час|мин|мес|month)',
            result["header_text"], re.IGNORECASE
        )
        if duration_match:
            val = duration_match.group(1)
            unit = duration_match.group(2)
            unit_map = {
                "day": "дн", "дн": "дн", "month": "мес", "мес": "мес",
                "hour": "ч", "час": "ч", "min": "мин", "мин": "мин",
            }
            result["test_duration"] = f"{val} {unit_map.get(unit, unit)}"

    if result["test_duration"] and not result["duration"]:
        result["duration"] = result["test_duration"]

    # Extract configs
    result["configs"] = _extract_configs(text)

    # Try base64 decode
    if not result["configs"]:
        cleaned = text.replace("\n", "").replace("\r", "").strip()
        for attempt_pad in (True, False):
            try:
                if attempt_pad:
                    padding = 4 - len(cleaned) % 4
                    if padding != 4:
                        cleaned_padded = cleaned + "=" * padding
                    else:
                        cleaned_padded = cleaned
                else:
                    cleaned_padded = cleaned
                decoded = base64.b64decode(cleaned_padded).decode("utf-8", errors="ignore")
                decoded_configs = _extract_configs(decoded)
                if decoded_configs:
                    result["configs"] = decoded_configs
                    break
            except Exception:
                continue

    return result



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 7: SOURCES — 100+ subscription sources in 10 groups
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def build_sources():
    """
    Build ordered dictionary of all subscription sources.
    Each source: {name: [{"url": ..., "type": ..., "tag": ...}]}
    Groups in priority order for Russian RKN whitelist compatibility.
    """
    sources = OrderedDict()

    # ════════════════════════════════════════════════════════════
    #  1. RUSSIA / WHITELISTS (highest priority for RU users)
    # ════════════════════════════════════════════════════════════
    sources["RU:igareck-WL-1"] = [
        {"url": "https://cdn.jsdelivr.net/gh/igareck/vpn-configs-for-russia@main/Vless-Reality-White-Lists-Rus-Mobile.txt", "type": "cdn", "tag": "WL"},
    ]
    sources["RU:igareck-WL-2"] = [
        {"url": "https://cdn.jsdelivr.net/gh/igareck/vpn-configs-for-russia@main/Vless-Reality-White-Lists-Rus-Mobile-2.txt", "type": "cdn", "tag": "WL"},
    ]
    sources["RU:igareck-BLACK"] = [
        {"url": "https://cdn.jsdelivr.net/gh/igareck/vpn-configs-for-russia@main/BLACK_VLESS_RUS.txt", "type": "cdn", "tag": "RU"},
        {"url": "https://cdn.jsdelivr.net/gh/igareck/vpn-configs-for-russia@main/BLACK_VLESS_RUS_mobile.txt", "type": "cdn", "tag": "RU"},
        {"url": "https://cdn.jsdelivr.net/gh/igareck/vpn-configs-for-russia@main/BLACK_SS+All_RUS.txt", "type": "cdn", "tag": "RU"},
    ]
    sources["RU:goida-1"] = [
        {"url": "https://cdn.jsdelivr.net/gh/AvenCores/goida-vpn-configs@main/githubmirror/1.txt", "type": "cdn", "tag": "RU"},
    ]
    sources["RU:goida-4"] = [
        {"url": "https://raw.githubusercontent.com/AvenCores/goida-vpn-configs/refs/heads/main/githubmirror/4.txt", "type": "github", "tag": "RU"},
    ]

    # ════════════════════════════════════════════════════════════
    #  2. ANTI-DPI (XHTTP, HTTPUpgrade, TCP Reality)
    # ════════════════════════════════════════════════════════════
    sources["ANTI:xhttp"] = [
        {"url": "https://cdn.jsdelivr.net/gh/mohamadfg-dev/telegram-v2ray-configs-collector@main/category/xhttp.txt", "type": "cdn", "tag": "ANTI-DPI"},
    ]
    sources["ANTI:httpupgrade"] = [
        {"url": "https://cdn.jsdelivr.net/gh/mohamadfg-dev/telegram-v2ray-configs-collector@main/category/httpupgrade.txt", "type": "cdn", "tag": "ANTI-DPI"},
    ]
    sources["ANTI:tcp"] = [
        {"url": "https://raw.githubusercontent.com/mohamadfg-dev/telegram-v2ray-configs-collector/refs/heads/main/category/TCP.txt", "type": "github", "tag": "ANTI-DPI"},
    ]

    # ════════════════════════════════════════════════════════════
    #  3. TELEGRAM COLLECTORS (12 countries via mohamadfg)
    # ════════════════════════════════════════════════════════════
    tg_countries = [
        ("Russia", "Russia.txt"),
        ("Germany", "Germany.txt"),
        ("Netherlands", "Netherlands.txt"),
        ("Finland", "Finland.txt"),
        ("France", "France.txt"),
        ("Poland", "Poland.txt"),
        ("Sweden", "Sweden.txt"),
        ("UK", "United%20Kingdom.txt"),
        ("US", "U.S.%20Virgin%20Islands.txt"),
        ("Turkey", "Turkey.txt"),
        ("Iran", "Iran.txt"),
        ("UAE", "United%20Arab%20Emirates.txt"),
    ]
    for country, filename in tg_countries:
        key = f"TG:mohamadfg-{country}"
        sources[key] = [
            {"url": f"https://cdn.jsdelivr.net/gh/mohamadfg-dev/telegram-v2ray-configs-collector@main/category/{filename}", "type": "cdn", "tag": f"TG-{country[:3].upper()}"},
        ]

    # ════════════════════════════════════════════════════════════
    #  4. LARGE AGGREGATORS
    # ════════════════════════════════════════════════════════════
    sources["AGG:barry-far-vless"] = [
        {"url": "https://cdn.jsdelivr.net/gh/barry-far/V2ray-Configs@main/Splitted-By-Protocol/vless.txt", "type": "cdn", "tag": "AGG"},
    ]
    sources["AGG:barry-far-vmess"] = [
        {"url": "https://cdn.jsdelivr.net/gh/barry-far/V2ray-Configs@main/Splitted-By-Protocol/vmess.txt", "type": "cdn", "tag": "AGG"},
    ]
    sources["AGG:barry-far-trojan"] = [
        {"url": "https://cdn.jsdelivr.net/gh/barry-far/V2ray-Configs@main/Splitted-By-Protocol/trojan.txt", "type": "cdn", "tag": "AGG"},
    ]
    sources["AGG:barry-far-ss"] = [
        {"url": "https://cdn.jsdelivr.net/gh/barry-far/V2ray-Configs@main/Splitted-By-Protocol/ss.txt", "type": "cdn", "tag": "AGG"},
    ]
    sources["AGG:barry-far-ssr"] = [
        {"url": "https://raw.githubusercontent.com/barry-far/V2ray-Configs/main/Splitted-By-Protocol/ssr.txt", "type": "github", "tag": "AGG"},
    ]
    sources["AGG:barry-far-hy2"] = [
        {"url": "https://cdn.jsdelivr.net/gh/barry-far/V2ray-Configs@main/Splitted-By-Protocol/hysteria2.txt", "type": "cdn", "tag": "AGG"},
    ]
    sources["AGG:barry-far-all"] = [
        {"url": "https://cdn.jsdelivr.net/gh/barry-far/V2ray-Configs@main/All_Configs_Sub.txt", "type": "cdn", "tag": "AGG"},
    ]
    sources["AGG:MahsaNet"] = [
        {"url": "https://cdn.jsdelivr.net/gh/MahsaNetConfigTopic/config@main/xray_final.txt", "type": "cdn", "tag": "AGG"},
    ]
    sources["AGG:MatinGhanbari-ALL"] = [
        {"url": "https://cdn.jsdelivr.net/gh/MatinGhanbari/v2ray-configs@main/subscriptions/v2ray/all_sub.txt", "type": "cdn", "tag": "AGG"},
        {"url": "https://cdn.jsdelivr.net/gh/MatinGhanbari/v2ray-configs@main/subscriptions/v2ray/super-sub.txt", "type": "cdn", "tag": "AGG"},
    ]
    sources["AGG:MatinGhanbari-FILT"] = [
        {"url": "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/vless.txt", "type": "github", "tag": "AGG"},
        {"url": "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/vmess.txt", "type": "github", "tag": "AGG"},
        {"url": "https://raw.githubusercontent.com/MatinGhanbari/v2ray-configs/main/subscriptions/filtered/subs/ss.txt", "type": "github", "tag": "AGG"},
    ]
    sources["AGG:ebrasha"] = [
        {"url": "https://cdn.jsdelivr.net/gh/ebrasha/free-v2ray-public-list@main/V2Ray-Config-By-EbraSha.txt", "type": "cdn", "tag": "AGG"},
    ]
    sources["AGG:Delta-Kronecker"] = [
        {"url": "https://cdn.jsdelivr.net/gh/Delta-Kronecker/V2ray-Config@main/sub.txt", "type": "cdn", "tag": "AGG"},
    ]

    # ════════════════════════════════════════════════════════════
    #  5. SCRAPER (10ium: countries + protocols)
    # ════════════════════════════════════════════════════════════
    ium_countries = [
        ("Russia", "Russia"), ("Germany", "Germany"), ("Netherlands", "Netherlands"),
        ("USA", "USA"), ("France", "France"), ("Finland", "Finland"),
        ("UK", "UK"), ("Poland", "Poland"), ("Sweden", "Sweden"), ("Turkey", "Turkey"),
    ]
    for label, fname in ium_countries:
        sources[f"SC:10ium-{label}"] = [
            {"url": f"https://cdn.jsdelivr.net/gh/10ium/ScrapeAndCategorize@main/output_configs/{fname}.txt", "type": "cdn", "tag": f"SC-{label[:3].upper()}"},
        ]
    sources["SC:10ium-Vless"] = [
        {"url": "https://cdn.jsdelivr.net/gh/10ium/ScrapeAndCategorize@main/output_configs/Vless.txt", "type": "cdn", "tag": "SC"},
    ]
    sources["SC:10ium-Hysteria2"] = [
        {"url": "https://cdn.jsdelivr.net/gh/10ium/ScrapeAndCategorize@main/output_configs/Hysteria2.txt", "type": "cdn", "tag": "SC"},
    ]
    sources["SC:10ium-Trojan"] = [
        {"url": "https://raw.githubusercontent.com/10ium/ScrapeAndCategorize/refs/heads/main/output_configs/Trojan.txt", "type": "github", "tag": "SC"},
    ]
    sources["SC:10ium-SS"] = [
        {"url": "https://raw.githubusercontent.com/10ium/ScrapeAndCategorize/refs/heads/main/output_configs/ShadowSocks.txt", "type": "github", "tag": "SC"},
    ]

    # ════════════════════════════════════════════════════════════
    #  6. COLLECTORS (yebekhe, mahdibland, SoliSpirit, Epodonios, etc.)
    # ════════════════════════════════════════════════════════════
    sources["COLL:yebekhe-mix"] = [
        {"url": "https://cdn.jsdelivr.net/gh/yebekhe/TelegramV2rayCollector@main/sub/base64/mix", "type": "cdn", "tag": "COLL"},
    ]
    sources["COLL:yebekhe-reality"] = [
        {"url": "https://cdn.jsdelivr.net/gh/yebekhe/TelegramV2rayCollector@main/sub/base64/reality", "type": "cdn", "tag": "COLL"},
    ]
    sources["COLL:yebekhe-hy2"] = [
        {"url": "https://cdn.jsdelivr.net/gh/yebekhe/TelegramV2rayCollector@main/sub/base64/hy2", "type": "cdn", "tag": "COLL"},
    ]
    sources["COLL:yebekhe-normal"] = [
        {"url": "https://raw.githubusercontent.com/yebekhe/TelegramV2rayCollector/main/sub/normal/mix", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:mahdibland-b64"] = [
        {"url": "https://cdn.jsdelivr.net/gh/mahdibland/V2RayAggregator@master/sub/sub_merge_base64.txt", "type": "cdn", "tag": "COLL"},
    ]
    sources["COLL:mahdibland-plain"] = [
        {"url": "https://cdn.jsdelivr.net/gh/mahdibland/V2RayAggregator@master/sub/sub_merge.txt", "type": "cdn", "tag": "COLL"},
    ]
    sources["COLL:mahdibland-trojan"] = [
        {"url": "https://raw.githubusercontent.com/mahdibland/ShadowsocksAggregator/master/sub/splitted/trojan.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:SoliSpirit"] = [
        {"url": "https://cdn.jsdelivr.net/gh/SoliSpirit/v2ray-configs@main/Protocols/vless.txt", "type": "cdn", "tag": "COLL"},
        {"url": "https://cdn.jsdelivr.net/gh/SoliSpirit/v2ray-configs@main/Protocols/vmess.txt", "type": "cdn", "tag": "COLL"},
        {"url": "https://cdn.jsdelivr.net/gh/SoliSpirit/v2ray-configs@main/Protocols/ss.txt", "type": "cdn", "tag": "COLL"},
    ]
    sources["COLL:Epodonios-v2ray"] = [
        {"url": "https://cdn.jsdelivr.net/gh/Epodonios/v2ray-configs@main/Sub1.txt", "type": "cdn", "tag": "COLL"},
        {"url": "https://cdn.jsdelivr.net/gh/Epodonios/v2ray-configs@main/Sub2.txt", "type": "cdn", "tag": "COLL"},
        {"url": "https://cdn.jsdelivr.net/gh/Epodonios/v2ray-configs@main/Sub3.txt", "type": "cdn", "tag": "COLL"},
    ]
    sources["COLL:Epodonios-DE"] = [
        {"url": "https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/refs/heads/main/sub/Germany/config.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:Epodonios-NL"] = [
        {"url": "https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/refs/heads/main/sub/Netherlands/config.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:Epodonios-FR"] = [
        {"url": "https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/refs/heads/main/sub/France/config.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:Epodonios-PL"] = [
        {"url": "https://raw.githubusercontent.com/Epodonios/bulk-xray-v2ray-vless-vmess-...-configs/refs/heads/main/sub/Poland/config.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:hamedcode"] = [
        {"url": "https://raw.githubusercontent.com/hamedcode/port-based-v2ray-configs/main/sub/vless.txt", "type": "github", "tag": "COLL"},
        {"url": "https://raw.githubusercontent.com/hamedcode/port-based-v2ray-configs/main/sub/vmess.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:nscl5"] = [
        {"url": "https://raw.githubusercontent.com/nscl5/5/refs/heads/main/configs/all.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:Danialsamadi"] = [
        {"url": "https://raw.githubusercontent.com/Danialsamadi/v2go/refs/heads/main/AllConfigsSub.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:F0rc3Run"] = [
        {"url": "https://raw.githubusercontent.com/F0rc3Run/F0rc3Run/refs/heads/main/Best-Results/proxies.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:F0rc3Run-split"] = [
        {"url": "https://raw.githubusercontent.com/F0rc3Run/F0rc3Run/main/splitted-by-protocol/vless.txt", "type": "github", "tag": "COLL"},
        {"url": "https://raw.githubusercontent.com/F0rc3Run/F0rc3Run/main/splitted-by-protocol/shadowsocks.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:Firmfox"] = [
        {"url": "https://raw.githubusercontent.com/Firmfox/Proxify/refs/heads/main/v2ray_configs/mixed/subscription-1.txt", "type": "github", "tag": "COLL"},
        {"url": "https://raw.githubusercontent.com/Firmfox/Proxify/refs/heads/main/v2ray_configs/mixed/subscription-2.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:4n0nymou3"] = [
        {"url": "https://raw.githubusercontent.com/4n0nymou3/ss-config-updater/refs/heads/main/configs.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:ebrasha-vmess"] = [
        {"url": "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/vmess_configs.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:ebrasha-ss"] = [
        {"url": "https://raw.githubusercontent.com/ebrasha/free-v2ray-public-list/refs/heads/main/ss_configs.txt", "type": "github", "tag": "COLL"},
    ]
    sources["COLL:NiREvil-wg"] = [
        {"url": "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/sub/v2rayng-wg.txt", "type": "github", "tag": "COLL"},
        {"url": "https://raw.githubusercontent.com/NiREvil/vless/refs/heads/main/sub/nekobox-wg.txt", "type": "github", "tag": "COLL"},
    ]

    # ════════════════════════════════════════════════════════════
    #  7. MISC (mfuu, ermaozi, peasoft, sashalsk, etc.)
    # ════════════════════════════════════════════════════════════
    sources["MISC:mfuu"] = [
        {"url": "https://cdn.jsdelivr.net/gh/mfuu/v2ray@master/v2ray", "type": "cdn", "tag": "MISC"},
    ]
    sources["MISC:ermaozi"] = [
        {"url": "https://cdn.jsdelivr.net/gh/ermaozi/get_subscribe@main/subscribe/v2ray.txt", "type": "cdn", "tag": "MISC"},
    ]
    sources["MISC:peasoft"] = [
        {"url": "https://cdn.jsdelivr.net/gh/peasoft/ClientData@main/raw/v2ray", "type": "cdn", "tag": "MISC"},
    ]
    sources["MISC:sashalsk"] = [
        {"url": "https://cdn.jsdelivr.net/gh/sashalsk/V2Ray@main/V2Config_64Encode", "type": "cdn", "tag": "MISC"},
    ]
    sources["MISC:V2RayPool"] = [
        {"url": "https://cdn.jsdelivr.net/gh/V2RAYCONFIGSPOOL/V2RAY_SUB@main/v2ray_configs.txt", "type": "cdn", "tag": "MISC"},
    ]
    sources["MISC:rango"] = [
        {"url": "https://cdn.jsdelivr.net/gh/rango-cfs/NewCollector@main/v2ray_links.txt", "type": "cdn", "tag": "MISC"},
    ]
    sources["MISC:kobabi"] = [
        {"url": "https://cdn.jsdelivr.net/gh/liketolivefree/kobabi@main/sub.txt", "type": "cdn", "tag": "MISC"},
    ]
    sources["MISC:10ium-Fast"] = [
        {"url": "https://cdn.jsdelivr.net/gh/10ium/free-config@main/HighSpeed.txt", "type": "cdn", "tag": "MISC"},
    ]
    sources["MISC:Argh94-HY2"] = [
        {"url": "https://cdn.jsdelivr.net/gh/Argh94/V2RayAutoConfig@main/configs/Hysteria2.txt", "type": "cdn", "tag": "MISC"},
    ]
    sources["MISC:ndsphonemy-SPEED"] = [
        {"url": "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/refs/heads/main/speed.txt", "type": "github", "tag": "MISC"},
    ]
    sources["MISC:ndsphonemy-MOBILE"] = [
        {"url": "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/refs/heads/main/mobile.txt", "type": "github", "tag": "MISC"},
    ]
    sources["MISC:ndsphonemy-TUIC"] = [
        {"url": "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/refs/heads/main/hys-tuic.txt", "type": "github", "tag": "MISC"},
    ]
    sources["MISC:ndsphonemy-WG"] = [
        {"url": "https://raw.githubusercontent.com/ndsphonemy/proxy-sub/refs/heads/main/wg.txt", "type": "github", "tag": "MISC"},
    ]

    # ════════════════════════════════════════════════════════════
    #  8. GITLAB (freefq, Pawdroid)
    # ════════════════════════════════════════════════════════════
    sources["GL:freefq"] = [
        {"url": "https://gitlab.com/freefq/free/-/raw/master/v2", "type": "gitlab", "tag": "GL"},
    ]
    sources["GL:Pawdroid"] = [
        {"url": "https://gitlab.com/Pawdroid/Free-servers/-/raw/main/sub", "type": "gitlab", "tag": "GL"},
    ]

    # ════════════════════════════════════════════════════════════
    #  9. ADDITIONAL BACKUP SOURCES
    # ════════════════════════════════════════════════════════════
    sources["BK:V2RayPool2"] = [
        {"url": "https://raw.githubusercontent.com/V2RayCONFIGSPOOL/V2RAY_SUB/main/v2ray_configs.txt", "type": "github", "tag": "BK"},
    ]
    sources["BK:southxjp"] = [
        {"url": "https://raw.githubusercontent.com/southxjp/Proxy-rules/main/V2rayProxies.txt", "type": "github", "tag": "BK"},
    ]
    sources["BK:aiboboxx"] = [
        {"url": "https://raw.githubusercontent.com/aiboboxx/v2rayfree/main/v2", "type": "github", "tag": "BK"},
    ]
    sources["BK:peasoft2"] = [
        {"url": "https://cdn.jsdelivr.net/gh/peasoft/NoMoreWalls/master/list_raw.txt", "type": "cdn", "tag": "BK"},
    ]
    sources["BK:freefq2"] = [
        {"url": "https://cdn.jsdelivr.net/gh/freefq/free/master/v2", "type": "cdn", "tag": "BK"},
    ]

    return sources


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 8: TELEGRAM SCANNER
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TG_CHANNELS = [
    ("freevpnoptions", "Free VPN configs daily", "free,channel"),
    ("v2rayng_vless", "VLESS configs for v2rayNG", "vless,channel"),
    ("freenodeism", "Free VPN nodes", "free,channel"),
    ("ConfigV2ray", "V2Ray configs", "v2ray,channel"),
    ("V2RayCollector", "V2Ray aggregator", "aggregator,channel"),
    ("free_v2ray_config", "Free V2Ray configs", "free,v2ray"),
    ("v2rayng_free", "Free configs for v2rayNG", "free,v2rayng"),
    ("Vless_Telegram", "VLESS Telegram configs", "vless,channel"),
    ("proxyfree", "Free proxy configs", "free,proxy"),
    ("ShadowProxy66", "Shadow configs", "shadow,proxy"),
    ("MTConfig", "MTProto configs", "mtproto"),
    ("RealityVPN", "Reality VPN configs", "reality,channel"),
    ("Hysteria2_free", "Free Hysteria2 configs", "hy2,free"),
    ("Vpn_1_365", "Daily VPN configs", "daily,channel"),
    ("OutlineVPN_free", "Free Outline VPN", "outline,free"),
]


def scan_telegram_channels(max_channels=15):
    """
    Scan Telegram channels via t.me/s/ web interface.
    Extracts subscription URLs and base64-encoded configs.
    Returns (found_urls, found_configs).
    """
    found_urls = []
    found_configs = []
    channels_to_scan = TG_CHANNELS[:max_channels]
    info(f"Сканирование Telegram-каналов (максимум {max_channels})...")

    for i, (channel, desc, tags) in enumerate(channels_to_scan):
        if _interrupted:
            break
        url = f"https://t.me/s/{channel}"
        text = dl_text(url, timeout=10)
        if not text:
            verbose(f"TG @{channel}: нет данных")
            continue

        # Extract URLs
        url_pattern = r'https?://[^\s<>"\')\]]+(?:sub|config|vless|vmess|trojan|ss|hy2|hysteria)[^\s<>"\')\]]*'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        sub_urls = []
        for u in urls:
            u = u.rstrip(".,;:!?)")
            if u not in found_urls and len(u) > 20 and not u.startswith("https://t.me/"):
                sub_urls.append(u)
                found_urls.append(u)

        # Extract base64-encoded configs
        b64_pattern = r'(?:^|\s)([A-Za-z0-9+/=]{100,})(?:\s|$)'
        b64_matches = re.findall(b64_pattern, text)
        for b64_str in b64_matches:
            try:
                decoded = base64.b64decode(b64_str).decode("utf-8", errors="ignore")
                configs = _extract_configs(decoded)
                for cfg in configs:
                    if cfg not in found_configs:
                        found_configs.append(cfg)
            except Exception:
                pass

        if sub_urls or found_configs:
            source_label = f"@{channel}"
            for u in sub_urls:
                ok(f"TG {source_label}: подписка {u[:60]}...")
            if found_configs:
                ok(f"TG {source_label}: {len(found_configs)} конфигов")

        prog(i + 1, len(channels_to_scan), prefix="TG Scan: ")

    return found_urls, found_configs


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 9: CACHE — Load/save with full metadata
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def load_cache():
    """Load cache from disk. Returns dict or None."""
    try:
        if not os.path.exists(CACHE_FILE):
            return None
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return None
        if "configs" not in data or "timestamp" not in data:
            return None
        return data
    except Exception:
        return None


def save_cache(sub_results, all_configs=None, source_stats=None):
    """Save cache to disk with configs, sub metadata and source stats."""
    try:
        configs_to_save = all_configs or []
        if len(configs_to_save) > CACHE_MAX_CONFIGS:
            configs_to_save = configs_to_save[:CACHE_MAX_CONFIGS]

        compact_subs = []
        for sr in sub_results:
            compact_subs.append({
                "source": sr.get("source", ""),
                "tags": sr.get("tags", []),
                "sub_type": sr.get("sub_type", "unknown"),
                "upload": sr.get("upload", 0),
                "download": sr.get("download", 0),
                "total": sr.get("total", 0),
                "expire": sr.get("expire", 0),
                "duration": sr.get("duration", ""),
                "traffic_limit": sr.get("traffic_limit", ""),
                "test_duration": sr.get("test_duration", ""),
                "config_count": len(sr.get("configs", [])),
            })

        cache_data = {
            "timestamp": time.time(),
            "configs": configs_to_save,
            "sub_results": compact_subs,
            "source_stats": source_stats or {},
            "version": "9.0",
        }

        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=1)
    except Exception:
        pass


def cache_age_str(ts):
    """Return human-readable cache age string."""
    try:
        if not ts:
            return "unknown"
        age = time.time() - ts
        if age < 60:
            return f"{int(age)}s ago"
        elif age < 3600:
            return f"{int(age / 60)}m ago"
        elif age < 86400:
            return f"{int(age / 3600)}h ago"
        else:
            return f"{int(age / 86400)}d ago"
    except Exception:
        return "unknown"



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 10: ENGINE — Parallel download, validation, quality scoring
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _count_urls(sources):
    """Count total number of URLs across all sources."""
    total = 0
    for name, entries in sources.items():
        total += len(entries)
    return total


def fetch_all_sources(sources, dl_workers=MAX_DL_WORKERS):
    """
    Download all source URLs in parallel.
    Each URL tested INDIVIDUALLY (never assumes "no internet").
    Returns list of subscription result dicts.
    """
    total_urls = _count_urls(sources)
    sub_results = []

    tasks = []
    for name, entries in sources.items():
        for entry in entries:
            tasks.append((name, entry))

    _state["sources_tried"] = 0
    _state["sources_ok"] = 0
    _state["configs_found"] = 0

    def _fetch_one(task):
        name, entry = task
        url = entry.get("url", "")
        tag = entry.get("tag", "")
        text = dl_with_mirrors(url, timeout=DL_TIMEOUT)
        return name, url, tag, text

    completed = 0

    with ThreadPoolExecutor(max_workers=dl_workers) as executor:
        futures = {executor.submit(_fetch_one, task): task for task in tasks}
        for future in as_completed(futures):
            if _interrupted:
                break
            try:
                name, url, tag, text = future.result()
                completed += 1

                with _state["lock"]:
                    _state["sources_tried"] = completed

                # Track source stats
                with _source_stats_lock:
                    if name not in _source_stats:
                        _source_stats[name] = {"tried": 0, "ok": 0, "configs": 0, "alive": 0}
                    _source_stats[name]["tried"] += 1

                if text and len(text) > 10:
                    result = parse_subscription(text, name, [tag])
                    config_count = len(result["configs"])

                    with _state["lock"]:
                        _state["sources_ok"] += 1
                        _state["configs_found"] += config_count

                    with _source_stats_lock:
                        _source_stats[name]["ok"] += 1
                        _source_stats[name]["configs"] += config_count

                    sub_results.append(result)

                    verbose(f"[OK] {name}: {config_count} конфигов")

                    if completed % 5 == 0 or completed == total_urls:
                        prog(completed, total_urls, prefix="Download: ")
                else:
                    verbose(f"[SKIP] {name}: нет данных")
                    if completed % 5 == 0 or completed == total_urls:
                        prog(completed, total_urls, prefix="Download: ")

            except Exception as e:
                completed += 1
                with _state["lock"]:
                    _state["sources_tried"] = completed
                if completed % 5 == 0 or completed == total_urls:
                    prog(completed, total_urls, prefix="Download: ")

    prog(total_urls, total_urls, prefix="Download: ")
    return sub_results


def validate_configs(configs, timeout=PING_TIMEOUT, ping_workers=MAX_PING_WORKERS,
                    ping_count=DEFAULT_PING_COUNT, resolve_dns=False):
    """
    Validate configs with TCP ping. Multi-threaded. Supports multi-ping averaging.
    Returns list of (config, ping_ms, host, port, proto, country, transport, dpi_score).
    """
    if not configs:
        return []

    validated = []
    total = len(configs)
    _state["ping_done"] = 0
    _state["ping_total"] = total
    _state["ping_alive"] = 0
    _state["ping_dead"] = 0

    def _ping_one(config):
        host, port = _get_host_port(config)
        if not host or not port:
            return None
        # DNS resolve if requested
        if resolve_dns:
            resolved = _dns_resolve_cached(host)
            if resolved:
                ping_host = resolved
            else:
                ping_host = host
        else:
            ping_host = host
        ping_ms = tcp_ping_avg(ping_host, port, timeout, ping_count)
        return (config, ping_ms, host, port)

    done_count = 0

    with ThreadPoolExecutor(max_workers=ping_workers) as executor:
        futures = {executor.submit(_ping_one, cfg): cfg for cfg in configs}
        for future in as_completed(futures):
            if _interrupted:
                break
            try:
                result = future.result()
                done_count += 1

                with _state["lock"]:
                    _state["ping_done"] = done_count

                if result is not None:
                    config, ping_ms, host, port = result
                    proto = _get_proto(config)
                    country = _get_country(config)
                    transport = _get_transport(config)
                    dpi = _dpi_score(config)
                    validated.append((config, ping_ms, host, port, proto, country, transport, dpi))

                    if ping_ms > 0:
                        with _state["lock"]:
                            _state["ping_alive"] += 1
                    else:
                        with _state["lock"]:
                            _state["ping_dead"] += 1

                    # Track source reliability
                    with _config_sources_lock:
                        key = f"{proto}:{host}:{port}"
                        if key in _config_sources:
                            for src_name in _config_sources[key]:
                                with _source_stats_lock:
                                    if src_name in _source_stats:
                                        _source_stats[src_name]["alive"] += 1

                if done_count % 10 == 0 or done_count == total:
                    prog(done_count, total, prefix="Ping: ")

            except Exception:
                done_count += 1
                with _state["lock"]:
                    _state["ping_done"] = done_count
                if done_count % 10 == 0 or done_count == total:
                    prog(done_count, total, prefix="Ping: ")

    prog(total, total, prefix="Ping: ")
    return validated


def deduplicate(configs):
    """Remove duplicate configs. Deduplicates by proto:host:port."""
    seen = set()
    unique = []
    for config in configs:
        host, port = _get_host_port(config)
        proto = _get_proto(config)
        if host and port:
            key = f"{proto}:{host}:{port}"
        else:
            key = config.strip()[:200]
        if key not in seen:
            seen.add(key)
            unique.append(config)
    return unique


def track_config_sources(configs, source_name):
    """Track which sources provide which configs for duplicate detection."""
    with _config_sources_lock:
        for cfg in configs:
            host, port = _get_host_port(cfg)
            proto = _get_proto(cfg)
            if host and port:
                key = f"{proto}:{host}:{port}"
                if key not in _config_sources:
                    _config_sources[key] = []
                if source_name not in _config_sources[key]:
                    _config_sources[key].append(source_name)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 11: OUTPUT — Write all file types, reports, JSON, Clash, base64, grouped
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _quality_score(dpi_score, ping_ms):
    """
    Calculate quality score for sorting. Higher = better.
    With ping: dpi * 2 - ping * 0.1
    Without ping (-1): dpi * 2
    """
    if ping_ms < 0:
        return float(dpi_score * 2)
    return float(dpi_score * 2 - ping_ms * 0.1)


def _is_whitelist_compatible(link):
    """Check if config is compatible with RKN whitelist mode."""
    host, port = _get_host_port(link)
    if not host:
        return False
    for cdn in WHITELISTED_CDNS:
        if cdn in host.lower():
            return True
    try:
        frag = link.split("?")[1] if "?" in link else ""
        params = parse_qs(frag)
        sni = params.get("sni", [""])[0].lower()
        if sni in (s.lower() for s in WHITELIST_SNI):
            return True
    except Exception:
        pass
    return False


def _format_traffic(bytes_val):
    """Format bytes to human-readable traffic string."""
    if bytes_val <= 0:
        return "N/A"
    gb = bytes_val / (1024 ** 3)
    if gb >= 1:
        return f"{gb:.2f} GB"
    mb = bytes_val / (1024 ** 2)
    return f"{mb:.1f} MB"


def _format_expire(timestamp):
    """Format Unix timestamp to human-readable date."""
    if not timestamp or timestamp <= 0:
        return "N/A"
    try:
        dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return "N/A"


def _write_utf8(filepath, content):
    """Write content to file with UTF-8 BOM."""
    try:
        with open(filepath, "w", encoding="utf-8-sig") as f:
            f.write(content)
        return True
    except Exception:
        return False


def _write_raw(filepath, content):
    """Write content to file without BOM."""
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception:
        return False


def _config_to_clash(v_item):
    """Convert a config tuple to Clash proxy dict."""
    config, ping_ms, host, port, proto, country, transport, dpi = v_item
    try:
        no_frag = config.split("#")[0]
        frag = config.split("?")[1] if "?" in config else ""
        params = parse_qs(frag)
        name = _get_name(config)

        proxy = {"name": name, "type": PROTO_CLASH_NAME.get(proto, "socks5"),
                 "server": host, "port": int(port) if port else 0}

        if proto == "VLESS":
            uuid_match = re.search(r'[0-9a-f-]{36}', config.lower())
            proxy["uuid"] = uuid_match.group(0) if uuid_match else ""
            proxy["network"] = params.get("type", ["tcp"])[0]
            sec = params.get("security", ["none"])[0]
            proxy["tls"] = sec == "tls"
            if sec == "reality":
                proxy["tls"] = True
                proxy["reality"] = {"enabled": True}
                if params.get("sni"):
                    proxy["servername"] = params["sni"][0]
                if params.get("pbk"):
                    proxy["reality"]["public-key"] = params["pbk"][0]
                if params.get("sid"):
                    proxy["reality"]["short-id"] = params["sid"][0]
                if params.get("fp"):
                    proxy["client-fingerprint"] = params["fp"][0]
            if params.get("flow"):
                proxy["flow"] = params["flow"][0]
            if params.get("packetEncoding"):
                proxy["packet-encoding"] = params["packetEncoding"][0]
            net = params.get("type", ["tcp"])[0]
            if net == "ws":
                ws_opts = {}
                if params.get("path"):
                    ws_opts["path"] = params["path"][0]
                if params.get("host"):
                    ws_opts["headers"] = {"Host": params["host"][0]}
                proxy["ws-opts"] = ws_opts
            elif net == "grpc":
                proxy["grpc-opts"] = {"grpc-service-name": params.get("serviceName", [""])[0]}
            elif net == "xhttp":
                xhttp_opts = {}
                if params.get("path"):
                    xhttp_opts["path"] = params["path"][0]
                if params.get("mode"):
                    xhttp_opts["mode"] = params["mode"][0]
                proxy["xhttp-opts"] = xhttp_opts

        elif proto == "TROJAN":
            rest = no_frag.split("://", 1)[1].split("?")[0].split("#")[0]
            proxy["password"] = rest.split("@")[0] if "@" in rest else ""
            proxy["udp"] = True
            if params.get("sni"):
                proxy["sni"] = params["sni"][0]

        elif proto == "SS":
            rest = no_frag.split("://", 1)[1].split("?")[0].split("#")[0]
            try:
                decoded = base64.b64decode(rest + "==").decode("utf-8")
                method, passwd = decoded.split(":", 1)
                proxy["cipher"] = method
                proxy["password"] = passwd
            except Exception:
                pass

        elif proto == "VMess":
            try:
                b64_part = no_frag.split("://", 1)[1].split("?")[0]
                b64_clean = re.sub(r'[^A-Za-z0-9+/=]', '', b64_part)
                pad = 4 - len(b64_clean) % 4
                if pad != 4:
                    b64_clean += "=" * pad
                obj = json.loads(base64.b64decode(b64_clean).decode("utf-8"))
                proxy["uuid"] = obj.get("id", "")
                proxy["alterId"] = obj.get("aid", 0)
                proxy["cipher"] = obj.get("scy", "auto")
                net = obj.get("net", "tcp")
                proxy["network"] = net
                if net == "ws":
                    ws_opts = {}
                    if obj.get("path"):
                        ws_opts["path"] = obj["path"]
                    if obj.get("host"):
                        ws_opts["headers"] = {"Host": obj["host"]}
                    proxy["ws-opts"] = ws_opts
                elif net == "grpc":
                    proxy["grpc-opts"] = {"grpc-service-name": obj.get("path", "")}
                tls_obj = obj.get("tls", "")
                if tls_obj:
                    proxy["tls"] = True
                    if obj.get("sni"):
                        proxy["servername"] = obj["sni"]
            except Exception:
                pass

        elif proto == "HYSTERIA2":
            rest = no_frag.split("://", 1)[1].split("?")[0].split("#")[0]
            proxy["password"] = rest.split("@")[0] if "@" in rest else ""
            proxy["up"] = params.get("up", ["30"])[0]
            proxy["down"] = params.get("down", ["200"])[0]
            if params.get("sni"):
                proxy["sni"] = params["sni"][0]

        return proxy
    except Exception:
        return None


def write_output_files(validated, sub_results, top_n=0, args=None):
    """Write all output files: main, raw, stealth, whitelist, sub, report, grouped, clash, b64, json."""
    stealth_mode = args and args.get("stealth", False)
    whitelist_mode = args and args.get("whitelist", False)
    stealth_threshold = args.get("stealth_threshold", STEALTH_DEFAULT_THRESHOLD) if args else STEALTH_DEFAULT_THRESHOLD
    alive_only = args and args.get("alive_only", False)
    proto_filter = args.get("proto_filter", None) if args else None
    country_filter = args.get("country_filter", None) if args else None
    sort_mode = args.get("sort_mode", "quality") if args else "quality"

    # Sort
    if sort_mode == "ping":
        sorted_all = sorted(validated, key=lambda x: (x[1] if x[1] > 0 else 99999))
    elif sort_mode == "dpi":
        sorted_all = sorted(validated, key=lambda x: -x[7])
    elif sort_mode == "country":
        sorted_all = sorted(validated, key=lambda x: x[5].lower())
    elif sort_mode == "proto":
        sorted_all = sorted(validated, key=lambda x: x[4])
    else:
        sorted_all = sorted(validated, key=lambda x: _quality_score(x[7], x[1]), reverse=True)

    # Filters
    filtered = sorted_all
    if alive_only:
        filtered = [v for v in filtered if v[1] > 0]
    if proto_filter:
        proto_set = {p.strip().upper() for p in proto_filter}
        filtered = [v for v in filtered if v[4] in proto_set]
    if country_filter:
        country_set = {c.strip().upper() for c in country_filter}
        filtered = [v for v in filtered if _get_country_code(v[5]).upper() in country_set or
                    v[5].upper() in country_set]

    stealth_configs = [v for v in sorted_all if v[7] >= stealth_threshold]
    wl_configs = [v for v in sorted_all if _is_whitelist_compatible(v[0])]
    if top_n > 0:
        top_configs = filtered[:top_n]
    else:
        top_configs = filtered

    if stealth_mode:
        main_configs = stealth_configs
    elif whitelist_mode:
        main_configs = wl_configs
    else:
        main_configs = top_configs

    # 1. Main file
    _write_utf8(OUTPUT_MAIN, "\n".join(v[0] for v in main_configs) + "\n")

    # 2. Raw file (all, no filter)
    _write_raw(OUTPUT_RAW, "\n".join(v[0] for v in sorted_all) + "\n")

    # 3. Stealth file
    _write_utf8(OUTPUT_STEALTH, "\n".join(v[0] for v in stealth_configs) + "\n")

    # 4. Whitelist file
    _write_utf8(OUTPUT_WL, "\n".join(v[0] for v in wl_configs) + "\n")

    # 5. Subscription URLs file with metadata
    sub_lines = [f"# PROXY FORGE v9.0 \u2014 Subscription URLs",
                f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ""]
    for sr in sub_results:
        if sr.get("config_count", 0) > 0:
            stype = sr.get("sub_type", "unknown")
            parts = [sr.get("source", "")]
            if stype != "unknown":
                parts.append(f"type={stype}")
            if sr.get("total", 0) > 0:
                parts.append(f"limit={_format_traffic(sr['total'])}")
            if sr.get("expire", 0) > 0:
                parts.append(f"exp={_format_expire(sr['expire'])}")
            if sr.get("test_duration"):
                parts.append(f"duration={sr['test_duration']}")
            if sr.get("traffic_limit"):
                parts.append(f"traffic={sr['traffic_limit']}")
            parts.append(f"configs={sr.get('config_count', 0)}")
            sub_lines.append(f"# {' | '.join(parts)}")
    if hasattr(write_output_files, '_tg_urls'):
        for u in write_output_files._tg_urls:
            sub_lines.append(u)
    _write_utf8(OUTPUT_SUB, "\n".join(sub_lines) + "\n")

    # 6. Country-grouped output
    _write_grouped_file(sorted_all)

    # 7. Clash YAML output
    _write_clash_file(main_configs)

    # 8. Base64 subscription output
    _write_b64_file(main_configs)

    # 9. JSON export
    _write_json_file(sorted_all, sub_results)


def _write_grouped_file(validated):
    """Write country-grouped output with flags and statistics."""
    groups = OrderedDict()
    for v in validated:
        country = v[5]
        if country not in groups:
            groups[country] = []
        groups[country].append(v)

    now_msk = datetime.now(timezone(timedelta(hours=3))).strftime("%Y-%m-%d %H:%M (МСК)")
    proto_counts = {}
    for v in validated:
        proto_counts[v[4]] = proto_counts.get(v[4], 0) + 1

    lines = [
        f"# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550",
        f"#  \U0001f4e1 VPN CONFIGS FOR v2rayNG (Grouped by Country)",
        f"#  \u041e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u043e: {now_msk}",
        f"#  \u0412\u0441\u0435\u0433\u043e \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432: {len(validated)}",
        f"#  \u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u044b: {', '.join(f'{p}: {c}' for p, c in sorted(proto_counts.items()))}",
        f"#  \u0421\u0442\u0440\u0430\u043d: {len(groups)}",
        f"# \u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550\u2550",
        "",
    ]

    for country, items in groups.items():
        code = _get_country_code(country)
        flag = COUNTRY_FLAGS.get(code, "\U0001f30d")
        lines.append(f"# \u2500\u2500 {flag} {country} ({len(items)}) \u2500\u2500")
        for v in items:
            lines.append(v[0])
        lines.append("")

    _write_utf8(OUTPUT_GROUPED, "\n".join(lines))


def _write_clash_file(validated):
    """Write Clash/Sing-Box YAML config."""
    proxies = []
    for v in validated[:200]:
        proxy = _config_to_clash(v)
        if proxy:
            proxies.append(proxy)

    yaml_lines = [
        "proxies:",
    ]
    for p in proxies:
        yaml_lines.append(f"  - {json.dumps(p, ensure_ascii=False)}")

    _write_raw(OUTPUT_CLASH, "\n".join(yaml_lines))


def _write_b64_file(validated):
    """Write base64-encoded subscription file."""
    configs = [v[0] for v in validated]
    content = "\n".join(configs)
    encoded = base64.b64encode(content.encode("utf-8")).decode("ascii")
    _write_raw(OUTPUT_B64, encoded)


def _write_json_file(validated, sub_results):
    """Write structured JSON export."""
    data = {
        "generated": datetime.now().isoformat(),
        "total_configs": len(validated),
        "configs": [],
        "subscriptions": [],
        "source_stats": _source_stats,
    }
    for v in validated:
        data["configs"].append({
            "config": v[0],
            "ping_ms": v[1],
            "host": v[2],
            "port": v[3],
            "protocol": v[4],
            "country": v[5],
            "transport": v[6],
            "dpi_score": v[7],
            "quality_score": round(_quality_score(v[7], v[1]), 2),
            "alive": v[1] > 0,
        })
    for sr in sub_results:
        data["subscriptions"].append({
            "source": sr.get("source", ""),
            "sub_type": sr.get("sub_type", "unknown"),
            "traffic_limit": sr.get("traffic_limit", ""),
            "test_duration": sr.get("test_duration", ""),
            "config_count": len(sr.get("configs", [])),
            "upload": sr.get("upload", 0),
            "download": sr.get("download", 0),
            "total": sr.get("total", 0),
            "expire": sr.get("expire", 0),
        })
    _write_raw(OUTPUT_JSON, json.dumps(data, ensure_ascii=False, indent=2))


def write_report_file(report_text):
    """Write report to file."""
    _write_raw(OUTPUT_REPORT, report_text)


def build_report(sub_results, validated, elapsed):
    """Build full text report with per-source stats."""
    lines = []
    lines.append(f"{'=' * 60}")
    lines.append(f"  PROXY FORGE v9.0 \u2014 REPORT")
    lines.append(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"  Elapsed: {elapsed:.1f}s")
    lines.append(f"{'=' * 60}")
    lines.append("")

    total_configs = sum(len(sr.get("configs", [])) for sr in sub_results)
    alive = sum(1 for v in validated if v[1] > 0)
    dead = sum(1 for v in validated if v[1] <= 0)

    lines.append(f"  \u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u0432 \u043f\u0440\u043e\u0431\u043e\u0432\u0430\u043d\u043e:  {len(sub_results)}")
    lines.append(f"  \u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u0432 \u043e\u043a:         {_state['sources_ok']}")
    lines.append(f"  \u041d\u0430\u0439\u0434\u0435\u043d\u043e \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432:  {total_configs}")
    lines.append(f"  \u041f\u0440\u043e\u0432\u0435\u0440\u0435\u043d\u043e \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432: {len(validated)}")
    lines.append(f"  \u0416\u0438\u0432\u044b\u0445:               {alive}")
    lines.append(f"  \u041c\u0451\u0440\u0442\u0432\u044b\u0445:              {dead}")
    if len(validated) > 0:
        lines.append(f"  \u0416\u0438\u0432\u043e\u0441\u0442\u044c:             {alive * 100 // len(validated)}%")
    lines.append("")

    # By protocol
    proto_count = {}
    for v in validated:
        p = v[4]
        proto_count[p] = proto_count.get(p, 0) + 1
    lines.append(f"  {'\u2500' * 40}")
    lines.append(f"  \u041f\u041e \u041f\u0420\u041e\u0422\u041e\u041a\u041e\u041b\u0423:")
    for proto, count in sorted(proto_count.items(), key=lambda x: -x[1]):
        icon = PROTO_ICON.get(proto, "?")
        lines.append(f"    {icon} {proto:15s}  {count}")
    lines.append("")

    # By country (top 15)
    country_count = {}
    for v in validated:
        if v[1] > 0:
            c = v[5]
            country_count[c] = country_count.get(c, 0) + 1
    lines.append(f"  {'\u2500' * 40}")
    lines.append(f"  \u041f\u041e \u0421\u0422\u0420\u0410\u041d\u0415 (\u0436\u0438\u0432\u044b\u0435, top 15):")
    for country, count in sorted(country_count.items(), key=lambda x: -x[1])[:15]:
        code = _get_country_code(country)
        flag = COUNTRY_FLAGS.get(code, "\U0001f30d")
        bar = "\u2588" * min(count, 20)
        lines.append(f"    {flag} {country:20s} {count:4d}  {bar}")
    lines.append("")

    # Per-source report
    lines.append(f"  {'\u2500' * 40}")
    lines.append(f"  \u041f\u041e \u0418\u0421\u0422\u041e\u0427\u041d\u0418\u041a\u0410\u041c:")
    with _source_stats_lock:
        for src_name, stats in sorted(_source_stats.items()):
            if stats.get("tried", 0) > 0:
                ok_count = stats.get("ok", 0)
                cfg_count = stats.get("configs", 0)
                alive_count = stats.get("alive", 0)
                rate = ok_count * 100 // stats["tried"]
                lines.append(f"    [{rate:3d}%] {src_name:40s}  \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432: {cfg_count}")
    lines.append("")

    # Subscription metadata
    lines.append(f"  {'\u2500' * 40}")
    lines.append(f"  \u041c\u0415\u0422\u0410\u0414\u0410\u041d\u041d\u042b\u0415 \u041f\u041e\u0414\u041f\u0418\u0421\u041a\u0418:")
    for sr in sub_results:
        if sr.get("config_count", 0) > 0:
            stype = sr.get("sub_type", "unknown")
            parts = [sr.get("source", "")]
            if stype != "unknown":
                parts.append(f"[{stype}]")
            if sr.get("traffic_limit"):
                parts.append(f"limit={sr['traffic_limit']}")
            if sr.get("test_duration"):
                parts.append(f"test={sr['test_duration']}")
            if sr.get("total", 0) > 0:
                parts.append(f"total={_format_traffic(sr['total'])}")
            if sr.get("expire", 0) > 0:
                parts.append(f"exp={_format_expire(sr['expire'])}")
            parts.append(f"({sr.get('config_count', 0)} configs)")
            lines.append(f"    {' | '.join(parts)}")
    lines.append("")

    # Top 20 DPI-resistant
    sorted_by_dpi = sorted(validated, key=lambda x: -x[7])
    lines.append(f"  {'\u2500' * 40}")
    lines.append(f"  TOP-20 DPI-\u0423\u0421\u0422\u041e\u0419\u0427\u0418\u0412\u042b\u0425:")
    for i, v in enumerate(sorted_by_dpi[:20]):
        ping_str = "\u2014" if v[1] < 0 else ("DEAD" if v[1] == 0 else f"{v[1]:.0f}ms")
        lines.append(f"    {i + 1:2d}. {PROTO_ICON.get(v[4], '?')} {v[5]:15s} DPI:{v[7]:3d}  {ping_str:>8s}  {v[6]}")
    lines.append("")

    # Top 20 fastest
    alive_only = [v for v in validated if v[1] > 0]
    sorted_by_ping = sorted(alive_only, key=lambda x: x[1])
    lines.append(f"  {'\u2500' * 40}")
    lines.append(f"  TOP-20 \u0411\u042b\u0421\u0422\u0420\u042b\u0425:")
    for i, v in enumerate(sorted_by_ping[:20]):
        lines.append(f"    {i + 1:2d}. {PROTO_ICON.get(v[4], '?')} {v[5]:15s} {v[1]:6.0f}ms  DPI:{v[7]:3d}  {v[6]}")
    lines.append("")

    # Top 20 by quality
    sorted_by_quality = sorted(validated, key=lambda x: _quality_score(x[7], x[1]), reverse=True)
    lines.append(f"  {'\u2500' * 40}")
    lines.append(f"  TOP-20 \u041f\u041e \u041a\u0410\u0427\u0415\u0421\u0422\u0412\u0423:")
    for i, v in enumerate(sorted_by_quality[:20]):
        qs = _quality_score(v[7], v[1])
        ping_str = "\u2014" if v[1] < 0 else ("DEAD" if v[1] == 0 else f"{v[1]:.0f}ms")
        lines.append(f"    {i + 1:2d}. {PROTO_ICON.get(v[4], '?')} {v[5]:15s} Q:{qs:6.1f}  DPI:{v[7]:3d}  {ping_str:>8s}  {v[6]}")
    lines.append("")

    lines.append(f"{'=' * 60}")
    lines.append(f"  \u041a\u041e\u041d\u0415\u0426 \u041e\u0422\u0427\u0401\u0422\u0410")
    lines.append(f"{'=' * 60}")

    return "\n".join(lines)


def print_console_table(validated, top_n=50):
    """Print formatted console results table."""
    sorted_by_quality = sorted(validated, key=lambda x: _quality_score(x[7], x[1]), reverse=True)
    display = sorted_by_quality[:top_n]

    if not display:
        warn("\u041d\u0435\u0442 \u0432\u0430\u043b\u0438\u0434\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432 \u0434\u043b\u044f \u043e\u0442\u043e\u0431\u0440\u0430\u0436\u0435\u043d\u0438\u044f.")
        return

    if _quiet:
        return

    print(f"\n  {C.B}{'#':>3s}  {'Proto':6s}  {'Country':15s}  {'Ping':>7s}  {'DPI':>4s}  {'Quality':>7s}  Transport{C.R}")
    print(f"  {'\u2500' * 80}")

    for i, v in enumerate(display):
        if v[1] < 0:
            ping_str = f"{C.DIM}\u2014{C.R}"
        elif v[1] == 0:
            ping_str = f"{C.RED}DEAD{C.R}"
        else:
            ping_str = f"{C.GRN}{v[1]:.0f}ms{C.R}"
        dpi_color = C.GRN if v[7] >= 70 else (C.YEL if v[7] >= 40 else C.RED)
        qs = _quality_score(v[7], v[1])
        qs_color = C.GRN if qs >= 100 else (C.YEL if qs >= 50 else C.RED)
        icon = PROTO_ICON.get(v[4], "?")
        print(
            f"  {i + 1:3d}  {icon} {v[4]:<4s}  {v[5]:15s}  "
            f"{ping_str:>7s}  {dpi_color}{v[7]:3d}{C.R}  "
            f"{qs_color}{qs:7.1f}{C.R}  {C.DIM}{v[6]}{C.R}"
        )



# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 12: CLI — 20+ arguments
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _build_help_text():
    """Build help text with dynamic color substitution."""
    sep = "\u2500" * 56
    return f"""
{C.CYN}\u250c{sep}\u2510
\u2502  {C.B}\u26a1 PROXY FORGE v9.0 \u2014 Ultimate Edition{C.R}{C.CYN}                    \u2502
\u2502  100+ Sources | Clash | JSON | TG Scanner | DPI Score           \u2502
\u2514{sep}\u2518{C.R}

{C.B}\u0418\u0421\u041f\u041e\u041b\u042c\u0417\u041e\u0412\u0410\u041d\u0418\u0415:{C.R}
  python3 proxy_forge.py                        \u041f\u043e\u043b\u043d\u044b\u0439 \u0446\u0438\u043a\u043b: \u043f\u043e\u0438\u0441\u043a + \u043f\u0438\u043d\u0433 + \u0444\u0430\u0439\u043b\u044b
  python3 proxy_forge.py --fast                 \u0431\u0435\u0437 \u043f\u0438\u043d\u0433\u0430 (\u0431\u044b\u0441\u0442\u0440\u043e, ~15 \u0441\u0435\u043a)
  python3 proxy_forge.py --stealth              \u0442\u043e\u043b\u044c\u043a\u043e DPI-\u0443\u0441\u0442\u043e\u0439\u0447\u0438\u0432\u044b\u0435 \u043a\u043e\u043d\u0444\u0438\u0433\u0438
  python3 proxy_forge.py --whitelist            \u0434\u043b\u044f \u0440\u0435\u0436\u0438\u043c\u0430 \u0431\u0435\u043b\u044b\u0445 \u0441\u043f\u0438\u0441\u043a\u043e\u0432 \u0420\u041a\u041d
  python3 proxy_forge.py --top 50               \u0442\u043e\u043f-50 \u043b\u0443\u0447\u0448\u0438\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432
  python3 proxy_forge.py --timeout 4            \u0442\u0430\u0439\u043c\u0430\u0443\u0442 \u043f\u0438\u043d\u0433\u0430 4 \u0441\u0435\u043a\u0443\u043d\u0434\u044b
  python3 proxy_forge.py --subs-only            \u0442\u043e\u043b\u044c\u043a\u043e \u043f\u043e\u0438\u0441\u043a \u043f\u043e\u0434\u043f\u0438\u0441\u043e\u043a
  python3 proxy_forge.py --report               \u043e\u0442\u0447\u0451\u0442 \u0438\u0437 \u043a\u044d\u0448\u0430
  python3 proxy_forge.py --cache-only           \u0442\u043e\u043b\u044c\u043a\u043e \u0438\u0437 \u043a\u044d\u0448\u0430 (\u043e\u0444\u043b\u0430\u0439\u043d)
  python3 proxy_forge.py --no-cache             \u0438\u0433\u043d\u043e\u0440\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u043a\u044d\u0448
  python3 proxy_forge.py --tg-scan 15           \u0441\u043a\u0430\u043d\u0438\u0440\u043e\u0432\u0430\u0442\u044c 15 TG-\u043a\u0430\u043d\u0430\u043b\u043e\u0432

{C.B}\u0424\u0418\u041b\u042c\u0422\u0420\u042b:{C.R}
  python3 proxy_forge.py --proto vless,hy2     \u0444\u0438\u043b\u044c\u0442\u0440 \u043f\u043e \u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u0443
  python3 proxy_forge.py --country RU,DE,US     \u0444\u0438\u043b\u044c\u0442\u0440 \u043f\u043e \u0441\u0442\u0440\u0430\u043d\u0435
  python3 proxy_forge.py --alive-only           \u0442\u043e\u043b\u044c\u043a\u043e \u0436\u0438\u0432\u044b\u0435 \u043a\u043e\u043d\u0444\u0438\u0433\u0438
  python3 proxy_forge.py --sort ping            \u0441\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u043f\u043e \u043f\u0438\u043d\u0433\u0443
  python3 proxy_forge.py --sort dpi             \u0441\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u043f\u043e DPI
  python3 proxy_forge.py --sort country         \u0441\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u043f\u043e \u0441\u0442\u0440\u0430\u043d\u0435
  python3 proxy_forge.py --sort proto           \u0441\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u043f\u043e \u043f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u0443
  python3 proxy_forge.py --stealth-threshold 70 \u043f\u043e\u0440\u043e\u0433 DPI \u0434\u043b\u044f stealth-\u0440\u0435\u0436\u0438\u043c\u0430

{C.B}\u0412\u042b\u0412\u041e\u0414:{C.R}
  python3 proxy_forge.py --clash               Clash/Sing-Box YAML \u0444\u0430\u0439\u043b
  python3 proxy_forge.py --b64                 base64 \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0430
  python3 proxy_forge.py --json                JSON \u044d\u043a\u0441\u043f\u043e\u0440\u0442
  python3 proxy_forge.py --copy                \u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c \u0432 \u0431\u0443\u0444\u0435\u0440

{C.B}\u0414\u041e\u041f\u041e\u041b\u041d\u0418\u0422\u0415\u041b\u042c\u041d\u042b\u0415:{C.R}
  python3 proxy_forge.py --health               \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u0432\u0441\u0442\u0440\u043e\u0435\u043d\u043d\u044b\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432
  python3 proxy_forge.py --check-update         \u043f\u0440\u043e\u0432\u0435\u0440\u043a\u0430 \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0439
  python3 proxy_forge.py --resolve              DNS-\u0440\u0435\u0437\u043e\u043b\u044c\u0446\u0438\u044f \u043f\u0435\u0440\u0435\u0434 \u043f\u0438\u043d\u0433\u043e\u043c
  python3 proxy_forge.py --ping-count 3         \u0441\u0440\u0435\u0434\u043d\u0435\u0435 \u0437\u043d\u0430\u0447\u0435\u043d\u0438\u0435 3 \u043f\u0438\u043d\u0433\u043e\u0432
  python3 proxy_forge.py --quiet                \u043c\u0438\u043d\u0438\u043c\u0430\u043b\u044c\u043d\u044b\u0439 \u0432\u044b\u0432\u043e\u0434
  python3 proxy_forge.py -v / --verbose         \u043f\u043e\u0434\u0440\u043e\u0431\u043d\u044b\u0439 \u0432\u044b\u0432\u043e\u0434
"""


def parse_args():
    """Parse command-line arguments. Returns dict."""
    args = {
        "fast": False,
        "stealth": False,
        "whitelist": False,
        "top": 0,
        "timeout": PING_TIMEOUT,
        "no_cache": False,
        "cache_only": False,
        "subs_only": False,
        "report": False,
        "tg_scan": 0,
        "workers": MAX_DL_WORKERS,
        "ping_workers": MAX_PING_WORKERS,
        "proto_filter": None,
        "country_filter": None,
        "alive_only": False,
        "sort_mode": "quality",
        "stealth_threshold": STEALTH_DEFAULT_THRESHOLD,
        "clash": False,
        "b64": False,
        "json": False,
        "copy": False,
        "health": False,
        "check_update": False,
        "resolve": False,
        "ping_count": DEFAULT_PING_COUNT,
        "quiet": False,
        "verbose": False,
    }

    argv = sys.argv[1:]
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--help", "-h", "help"):
            print(_build_help_text())
            sys.exit(0)
        elif arg == "--fast":
            args["fast"] = True
        elif arg == "--stealth":
            args["stealth"] = True
        elif arg == "--whitelist":
            args["whitelist"] = True
        elif arg == "--top":
            i += 1
            if i < len(argv):
                args["top"] = int(argv[i])
        elif arg == "--timeout":
            i += 1
            if i < len(argv):
                args["timeout"] = int(argv[i])
        elif arg == "--no-cache":
            args["no_cache"] = True
        elif arg == "--cache-only":
            args["cache_only"] = True
        elif arg == "--subs-only":
            args["subs_only"] = True
        elif arg == "--report":
            args["report"] = True
        elif arg == "--tg-scan":
            i += 1
            if i < len(argv):
                args["tg_scan"] = int(argv[i])
        elif arg == "--workers":
            i += 1
            if i < len(argv):
                args["workers"] = int(argv[i])
        elif arg == "--ping-workers":
            i += 1
            if i < len(argv):
                args["ping_workers"] = int(argv[i])
        elif arg == "--proto":
            i += 1
            if i < len(argv):
                args["proto_filter"] = argv[i].split(",")
        elif arg == "--country":
            i += 1
            if i < len(argv):
                args["country_filter"] = argv[i].split(",")
        elif arg == "--alive-only":
            args["alive_only"] = True
        elif arg == "--sort":
            i += 1
            if i < len(argv):
                args["sort_mode"] = argv[i]
        elif arg == "--stealth-threshold":
            i += 1
            if i < len(argv):
                args["stealth_threshold"] = int(argv[i])
        elif arg == "--clash":
            args["clash"] = True
        elif arg == "--b64":
            args["b64"] = True
        elif arg == "--json":
            args["json"] = True
        elif arg == "--copy":
            args["copy"] = True
        elif arg == "--health":
            args["health"] = True
        elif arg == "--check-update":
            args["check_update"] = True
        elif arg == "--resolve":
            args["resolve"] = True
        elif arg == "--ping-count":
            i += 1
            if i < len(argv):
                args["ping_count"] = max(1, int(argv[i]))
        elif arg == "--quiet":
            args["quiet"] = True
        elif arg in ("-v", "--verbose"):
            args["verbose"] = True
        i += 1

    return args


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SECTION 13: MAIN — Pipeline orchestration with all modes
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _clipboard_copy(text):
    """Copy text to clipboard via termux-clipboard-set or xclip."""
    try:
        import subprocess
        # Try Termux first
        subprocess.run(["termux-clipboard-set"], input=text.encode(), check=True, timeout=5)
        return True
    except Exception:
        pass
    try:
        import subprocess
        subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True, timeout=5)
        return True
    except Exception:
        pass
    return False


def _auto_select_best(validated):
    """Select the best config (highest quality score among alive)."""
    alive = [v for v in validated if v[1] > 0]
    if not alive:
        return None
    sorted_q = sorted(alive, key=lambda x: _quality_score(x[7], x[1]), reverse=True)
    return sorted_q[0]


def main():
    """Main pipeline orchestration."""
    global _interrupted, _verbose, _quiet
    start_time = time.time()

    # Parse args first (needed for --quiet, --verbose)
    if len(sys.argv) < 2:
        pass  # Will print help after banner
    args = parse_args()
    _verbose = args.get("verbose", False)
    _quiet = args.get("quiet", False)

    # Banner
    if not _quiet:
        banner()

    if len(sys.argv) < 2:
        print(_build_help_text())

    # ── Health check mode ──
    if args["health"]:
        head("\u041f\u0420\u041e\u0412\u0415\u0420\u041a\u0410 \u0417\u0414\u041e\u0420\u041e\u0412\u042c\u042f \u0412\u0421\u0422\u0420\u041e\u0415\u041d\u041d\u042b\u0425 \u041a\u041e\u041d\u0424\u0418\u0413\u041e\u0412")
        ok(f"\u041f\u0440\u043e\u0432\u0435\u0440\u044f\u0435\u043c {len(EMBEDDED_CONFIGS)} \u0432\u0441\u0442\u0440\u043e\u0435\u043d\u043d\u044b\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432...")
        alive_count = 0
        dead_list = []
        for cfg in EMBEDDED_CONFIGS:
            host, port = _get_host_port(cfg)
            if not host or not port:
                dead_list.append((_get_name(cfg), "\u043d\u0435\u0442 \u0430\u0434\u0440\u0435\u0441\u0430"))
                continue
            ms = tcp_ping(host, port, args["timeout"])
            if ms > 0:
                alive_count += 1
                ok(f"  \u2713 {_get_name(cfg)}: {ms:.0f}ms")
            else:
                dead_list.append((_get_name(cfg), "\u043d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u0435\u043d"))
                err(f"  \u2717 {_get_name(cfg)}: DEAD")

        print(f"\n  {C.B}\u0418\u0422\u041e\u0413\u041e:{C.R} {C.GRN}{alive_count}{C.R}/{len(EMBEDDED_CONFIGS)} \u0436\u0438\u0432\u044b\u0445")
        if dead_list:
            print(f"\n  {C.DIM}\u041d\u0435\u0434\u043e\u0441\u0442\u0443\u043f\u043d\u044b\u0435:{C.R}")
            for name, reason in dead_list:
                print(f"    {C.RED}\u2717{C.R} {name} ({reason})")
        return

    # ── Auto-update check ──
    if args["check_update"]:
        head("\u041f\u0420\u041e\u0412\u0415\u0420\u041a\u0410 \u041e\u0411\u041d\u041e\u0412\u041b\u0415\u041d\u0418\u0419")
        cache = load_cache()
        if cache:
            ts = cache.get("timestamp", 0)
            age = cache_age_str(ts)
            configs_count = len(cache.get("configs", []))
            info(f"\u041a\u044d\u0448: {configs_count} \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432, \u0432\u043e\u0437\u0440\u0430\u0441\u0442: {age}")
            if time.time() - ts > 3600:
                ok("\u0420\u0435\u043a\u043e\u043c\u0435\u043d\u0434\u0443\u0435\u0442\u0441\u044f \u0437\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u044c \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 (\u043a\u044d\u0448 \u0441\u0442\u0430\u0440\u0435\u0435 1\u0447)")
            else:
                info("\u041a\u044d\u0448 \u0441\u0432\u0435\u0436\u0438\u0439, \u043e\u0431\u043d\u043e\u0432\u043b\u0435\u043d\u0438\u0435 \u043d\u0435 \u0442\u0440\u0435\u0431\u0443\u0435\u0442\u0441\u044f")
        else:
            err("\u041a\u044d\u0448 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. \u0417\u0430\u043f\u0443\u0441\u0442\u0438\u0442\u0435 \u043f\u043e\u043b\u043d\u044b\u0439 \u0446\u0438\u043a\u043b.")
        return

    # ── Load cache ──
    cache = None
    if not args["no_cache"]:
        cache = load_cache()
        if cache:
            age = cache_age_str(cache.get("timestamp", 0))
            cached_count = len(cache.get("configs", []))
            info(f"\u041a\u044d\u0448: {C.GRN}{cached_count}{C.R} \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432, \u0432\u043e\u0437\u0440\u0430\u0441\u0442: {age}")
        else:
            info(f"\u041a\u044d\u0448: {C.DIM}\u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d{C.R}")

    # ── Report mode ──
    if args["report"]:
        if not cache:
            err("\u041a\u044d\u0448 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0441\u043d\u0430\u0447\u0430\u043b\u0430 \u0431\u0435\u0437 --report.")
            sys.exit(1)
        head("\u041e\u0422\u0427\u0401\u0422 \u0418\u0417 \u041a\u042d\u0428\u0410")
        cached_configs = cache.get("configs", [])
        cached_subs = cache.get("sub_results", [])
        info(f"\u041a\u0435\u0448\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0435 \u043a\u043e\u043d\u0444\u0438\u0433\u0438: {len(cached_configs)}")
        info(f"\u041f\u043e\u0434\u043f\u0438\u0441\u043a\u0438: {len(cached_subs)}")
        for sr in cached_subs:
            if sr.get("config_count", 0) > 0:
                parts = [sr.get("source", "")]
                if sr.get("sub_type") != "unknown":
                    parts.append(f"[{sr['sub_type']}]")
                if sr.get("total", 0) > 0:
                    parts.append(f"limit={_format_traffic(sr['total'])}")
                if sr.get("test_duration"):
                    parts.append(f"test={sr['test_duration']}")
                parts.append(f"({sr.get('config_count', 0)} configs)")
                print(f"    {' | '.join(parts)}")
        sys.exit(0)

    # ── Cache-only mode ──
    if args["cache_only"]:
        if not cache:
            err("\u041a\u044d\u0448 \u043d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d. \u0421\u043d\u0430\u0447\u0430\u043b\u0430 \u0431\u0435\u0437 --cache-only.")
            sys.exit(1)
        head("\u0420\u0415\u0416\u0418\u041c \u0422\u041e\u041b\u042c\u041a\u041e \u0418\u0417 \u041a\u042d\u0428\u0410")
        all_configs = cache.get("configs", [])
        if not all_configs:
            err("\u041a\u044d\u0448 \u043f\u0443\u0441\u0442.")
            sys.exit(1)
        all_configs = deduplicate(all_configs)
        ok(f"\u0417\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u043e {len(all_configs)} \u043a\u0435\u0448\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432")

        if not args["fast"] and not args["subs_only"]:
            head("\u0412\u0430\u043b\u0438\u0434\u0430\u0446\u0438\u044f \u043a\u0435\u0448\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432")
            validated = validate_configs(all_configs, args["timeout"], args["ping_workers"],
                                       args["ping_count"], args["resolve"])
        else:
            validated = []
            for cfg in all_configs:
                host, port = _get_host_port(cfg)
                proto = _get_proto(cfg)
                country = _get_country(cfg)
                transport = _get_transport(cfg)
                dpi = _dpi_score(cfg)
                validated.append((cfg, -1, host or "?", port or 0, proto, country, transport, dpi))

        sub_results = cache.get("sub_results", [])
        elapsed = time.time() - start_time
        write_output_files(validated, sub_results, args["top"], args)
        report = build_report(sub_results, validated, elapsed)
        write_report_file(report)
        print_console_table(validated, min(args["top"] if args["top"] > 0 else 50, len(validated)))
        _print_summary(validated, elapsed, args)
        return

    # ── Scan Telegram channels ──
    tg_urls = []
    tg_configs = []
    if args["tg_scan"] > 0:
        head(f"Telegram Scanner ({args['tg_scan']} \u043a\u0430\u043d\u0430\u043b\u043e\u0432)")
        tg_urls, tg_configs = scan_telegram_channels(args["tg_scan"])
        ok(f"TG: \u043d\u0430\u0439\u0434\u0435\u043d\u043e {len(tg_urls)} URL, {len(tg_configs)} \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432")

    # ── Build sources + TG URLs ──
    sources = build_sources()
    if tg_urls:
        for i, url in enumerate(tg_urls[:20]):
            sources[f"TG-DISCOVERED:{i}"] = [
                {"url": url, "type": "tg", "tag": "TG-SCAN"},
            ]

    total_source_urls = _count_urls(sources)
    info(f"\u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u0432: {len(sources)} \u0433\u0440\u0443\u043f\u043f, {total_source_urls} URL")

    # ── Download all sources ──
    head("\u0417\u0430\u0433\u0440\u0443\u0437\u043a\u0430 \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u0432")
    sub_results = fetch_all_sources(sources, args["workers"])
    ok(f"\u0417\u0430\u0433\u0440\u0443\u0436\u0435\u043d\u043e: {_state['sources_ok']}/{_state['sources_tried']} \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u0432, {_state['configs_found']} \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432")

    # ── Collect all configs ──
    all_configs = []
    for sr in sub_results:
        all_configs.extend(sr.get("configs", []))
        track_config_sources(sr.get("configs", []), sr.get("source", ""))

    all_configs.extend(EMBEDDED_CONFIGS)
    info(f"+ {len(EMBEDDED_CONFIGS)} \u0432\u0441\u0442\u0440\u043e\u0435\u043d\u043d\u044b\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432")

    if tg_configs:
        all_configs.extend(tg_configs)
        info(f"+ {len(tg_configs)} TG \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432")

    if cache and not args["no_cache"]:
        cached_configs = cache.get("configs", [])
        if cached_configs:
            all_configs.extend(cached_configs)
            info(f"+ {len(cached_configs)} \u043a\u0435\u0448\u0438\u0440\u043e\u0432\u0430\u043d\u043d\u044b\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432")

    # ── Deduplicate ──
    head("\u0414\u0435\u0434\u0443\u043f\u043b\u0438\u043a\u0430\u0446\u0438\u044f")
    before = len(all_configs)
    all_configs = deduplicate(all_configs)
    removed = before - len(all_configs)
    ok(f"{before} -> {len(all_configs)} \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432 (\u0443\u0434\u0430\u043b\u0435\u043d\u043e {removed} \u0434\u0443\u0431\u043b\u0438\u043a\u0430\u0442\u043e\u0432)")

    if not all_configs:
        err("\u041d\u0435 \u043d\u0430\u0439\u0434\u0435\u043d\u043e \u043d\u0438 \u043e\u0434\u043d\u043e\u0433\u043e \u043a\u043e\u043d\u0444\u0438\u0433\u0430. \u041f\u0440\u043e\u0432\u0435\u0440\u044c\u0442\u0435 \u0438\u043d\u0442\u0435\u0440\u043d\u0435\u0442.")
        _write_utf8(OUTPUT_MAIN, "\n".join(EMBEDDED_CONFIGS) + "\n")
        ok(f"\u0417\u0430\u043f\u0438\u0441\u0430\u043d\u043e {len(EMBEDDED_CONFIGS)} \u0432\u0441\u0442\u0440\u043e\u0435\u043d\u043d\u044b\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432 \u0432 {OUTPUT_MAIN}")
        sys.exit(1)

    # ── Save cache ──
    head("\u0421\u043e\u0445\u0440\u0430\u043d\u0435\u043d\u0438\u0435 \u043a\u044d\u0448\u0430")
    with _source_stats_lock:
        stats_copy = dict(_source_stats)
    save_cache(sub_results, all_configs, stats_copy)
    ok(f"\u041a\u044d\u0448 \u0441\u043e\u0445\u0440\u0430\u043d\u0451\u043d ({len(all_configs)} \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432)")

    # ── Subscription metadata table ──
    sub_with_meta = [sr for sr in sub_results if sr.get("config_count", 0) > 0]
    if sub_with_meta:
        head("\u041c\u0435\u0442\u0430\u0434\u0430\u043d\u043d\u044b\u0435 \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0438")
        for sr in sub_with_meta[:30]:
            stype = sr.get("sub_type", "unknown")
            stype_icon = {
                "free": "\U0001f6ab", "trial": "\U0001f3af",
                "subscription": "\U0001f4cb", "expired": "\U0001f6d1",
            }.get(stype, "\u2022")
            parts = [f"{stype_icon} {sr.get('source', '')}"]
            if stype != "unknown":
                parts.append(f"[{stype}]")
            if sr.get("traffic_limit"):
                parts.append(f"limit={sr['traffic_limit']}")
            if sr.get("test_duration"):
                parts.append(f"test={sr['test_duration']}")
            if sr.get("total", 0) > 0:
                parts.append(f"total={_format_traffic(sr['total'])}")
            if sr.get("expire", 0) > 0:
                parts.append(f"exp={_format_expire(sr['expire'])}")
            parts.append(f"({sr.get('config_count', 0)} configs)")
            print(f"    {' | '.join(parts)}")

    # ── Validate with ping ──
    validated = []
    if not args["fast"] and not args["subs_only"]:
        head(f"TCP Ping \u0432\u0430\u043b\u0438\u0434\u0430\u0446\u0438\u044f (timeout={args['timeout']}s, workers={args['ping_workers']}, count={args['ping_count']})")
        validated = validate_configs(all_configs, args["timeout"], args["ping_workers"],
                                       args["ping_count"], args["resolve"])
        ok(f"\u0416\u0438\u0432\u044b\u0445: {C.GRN}{_state['ping_alive']}{C.R}, \u041c\u0451\u0440\u0442\u0432\u044b\u0445: {C.RED}{_state['ping_dead']}{C.R}")
    else:
        head("\u041f\u0440\u043e\u043f\u0443\u0441\u043a \u043f\u0438\u043d\u0433\u0430 (\u0431\u044b\u0441\u0442\u0440\u044b\u0439 \u0440\u0435\u0436\u0438\u043c)")
        for cfg in all_configs:
            host, port = _get_host_port(cfg)
            proto = _get_proto(cfg)
            country = _get_country(cfg)
            transport = _get_transport(cfg)
            dpi = _dpi_score(cfg)
            validated.append((cfg, -1, host or "?", port or 0, proto, country, transport, dpi))

    # ── Write output files ──
    head("\u0417\u0430\u043f\u0438\u0441\u044c \u0444\u0430\u0439\u043b\u043e\u0432")
    write_output_files._tg_urls = tg_urls
    write_output_files(validated, sub_results, args["top"], args)

    main_count = sum(1 for v in validated if True)
    ok(f"{C.CYN}\u0441\u0435\u0440\u0432{C.R}: \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 \u0444\u0430\u0439\u043b")
    ok(f"{C.CYN}\u0441\u0435\u0440\u0432_raw.txt{C.R}: \u0432\u0441\u0435 \u043a\u043e\u043d\u0444\u0438\u0433\u0438")
    ok(f"{C.CYN}\u0441\u0435\u0440\u0432_stealth.txt{C.R}: DPI >= {args['stealth_threshold']}")
    ok(f"{C.CYN}\u0441\u0435\u0440\u0432_whitelist.txt{C.R}: \u0434\u043b\u044f \u0431\u0435\u043b\u044b\u0445 \u0441\u043f\u0438\u0441\u043a\u043e\u0432 \u0420\u041a\u041d")
    ok(f"{C.CYN}\u0441\u0435\u0440\u0432_grouped.txt{C.R}: \u043f\u043e \u0441\u0442\u0440\u0430\u043d\u0430\u043c")
    ok(f"{C.CYN}\u0441\u0435\u0440\u0432_clash.yaml{C.R}: Clash \u0444\u043e\u0440\u043c\u0430\u0442")
    ok(f"{C.CYN}\u0441\u0435\u0440\u0432_b64.txt{C.R}: base64 \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0430")
    ok(f"{C.CYN}\u0441\u0435\u0440\u0438_data.json{C.R}: JSON \u044d\u043a\u0441\u043f\u043e\u0440\u0442")

    # ── Build and write report ──
    elapsed = time.time() - start_time
    report = build_report(sub_results, validated, elapsed)
    write_report_file(report)

    # ── Console table ──
    head("\u0420\u0435\u0437\u0443\u043b\u044c\u0442\u0430\u0442\u044b (\u0441\u043e\u0440\u0442\u0438\u0440\u043e\u0432\u043a\u0430 \u043f\u043e \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u0443)")
    display_top = args["top"] if args["top"] > 0 else 50
    print_console_table(validated, display_top)

    # ── Summary ──
    _print_summary(validated, elapsed, args)

    # ── Clipboard copy ──
    if args["copy"]:
        head("\u041a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u0435 \u0432 \u0431\u0443\u0444\u0435\u0440")
        best = _auto_select_best(validated)
        if best:
            if _clipboard_copy(best[0]):
                ok(f"\u0421\u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d \u043b\u0443\u0447\u0448\u0438\u0439: {best[5]} ({best[1]:.0f}ms)")
            else:
                warn("\u041d\u0435 \u0443\u0434\u0430\u043b\u043e\u0441\u044c \u0441\u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u0442\u044c (\u0443\u0441\u0442\u0430\u043d\u043e\u0432\u0438\u0442\u0435 termux-clipboard-set \u0438\u043b\u0438 xclip)")
        else:
            err("\u041d\u0435\u0442 \u0436\u0438\u0432\u044b\u0445 \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432 \u0434\u043b\u044f \u043a\u043e\u043f\u0438\u0440\u043e\u0432\u0430\u043d\u0438\u044f")


def _print_summary(validated, elapsed, args):
    """Print final summary and v2rayNG import instructions."""
    alive = sum(1 for v in validated if v[1] > 0)
    not_pinged = sum(1 for v in validated if v[1] < 0)
    dead = sum(1 for v in validated if v[1] == 0)
    total = len(validated)

    if _quiet:
        return

    print(f"\n  {C.B}{'=' * 60}{C.R}")
    print(f"  {C.B}\u0418\u0422\u041e\u0413\u0418{C.R}")
    print(f"  {C.B}{'=' * 60}{C.R}")
    print(f"    \u0412\u0440\u0435\u043c\u044f:              {C.CYN}{elapsed:.1f}s{C.R}")
    print(f"    \u0418\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u0432:          {_state['sources_ok']}/{_state['sources_tried']}")
    print(f"    \u041d\u0430\u0439\u0434\u0435\u043d\u043e \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432:  {C.CYN}{total}{C.R}")
    if not_pinged > 0:
        print(f"    {C.DIM}\u041f\u0438\u043d\u0433 \u043d\u0435 \u043f\u0440\u043e\u0432\u0435\u0440\u044f\u043b\u0441\u044f:  {not_pinged}{C.R}")
    else:
        print(f"    \u0416\u0438\u0432\u044b\u0445:             {C.GRN}{alive}{C.R}")
        print(f"    \u041c\u0451\u0440\u0442\u0432\u044b\u0445:            {C.RED}{dead}{C.R}")
        if total > 0:
            print(f"    \u0416\u0438\u0432\u043e\u0441\u0442\u044c:          {C.GRN}{alive * 100 // total}%{C.R}")

    print(f"\n  {C.B}\u0424\u0410\u0419\u041b\u042b:{C.R}")
    print(f"    {C.GRN}\u0441\u0435\u0440\u0432{C.R}                  \u2014 \u043e\u0441\u043d\u043e\u0432\u043d\u043e\u0439 (\u043b\u0443\u0447\u0448\u0438\u0435 \u043a\u043e\u043d\u0444\u0438\u0433\u0438)")
    print(f"    {C.GRN}\u0441\u0435\u0440\u0432_raw.txt{C.R}          \u2014 \u0432\u0441\u0435 \u043a\u043e\u043d\u0444\u0438\u0433\u0438")
    print(f"    {C.GRN}\u0441\u0435\u0440\u0432_stealth.txt{C.R}    \u2014 DPI-\u0443\u0441\u0442\u043e\u0439\u0447\u0438\u0432\u044b\u0435")
    print(f"    {C.GRN}\u0441\u0435\u0440\u0432_whitelist.txt{C.R} \u2014 \u0434\u043b\u044f \u0431\u0435\u043b\u044b\u0445 \u0441\u043f\u0438\u0441\u043a\u043e\u0432 \u0420\u041a\u041d")
    print(f"    {C.GRN}\u0441\u0435\u0440\u0432_grouped.txt{C.R}    \u2014 \u043f\u043e \u0441\u0442\u0440\u0430\u043d\u0430\u043c")
    print(f"    {C.GRN}\u0441\u0435\u0440\u0432_clash.yaml{C.R}     \u2014 Clash/Sing-Box")
    print(f"    {C.GRN}\u0441\u0435\u0440\u0432_b64.txt{C.R}        \u2014 base64 \u043f\u043e\u0434\u043f\u0438\u0441\u043a\u0430")
    print(f"    {C.GRN}\u0441\u0435\u0440\u0438_data.json{C.R}       \u2014 JSON \u044d\u043a\u0441\u043f\u043e\u0440\u0442")
    print(f"    {C.GRN}\u0441\u0435\u0440\u0432_report.txt{C.R}     \u2014 \u043f\u043e\u043b\u043d\u044b\u0439 \u043e\u0442\u0447\u0451\u0442")

    print(f"\n  {C.B}\u0418\u041c\u041f\u041e\u0420\u0422 \u0412 v2rayNG:{C.R}")
    print(f"    1. cat {C.CYN}\u0441\u0435\u0440\u0432{C.R} | termux-clipboard-set")
    print(f"    2. v2rayNG \u2192 Clipboard \u2192 Import from Clipboard")
    print(f"    3. \u0418\u043b\u0438: {C.CYN}cp \u0441\u0435\u0440\u0432 /sdcard/{C.R}")
    print(f"\n  {C.B}\u0421\u041e\u0417\u0414\u0410\u041d\u0418\u0415:{C.R}")
    print(f"    {C.GRN}\u0421\u0446\u0435\u043d\u0438\u0440\u043e\u0432\u0430\u043d\u043e {len(_source_stats)} \u0438\u0441\u0442\u043e\u0447\u043d\u0438\u043a\u043e\u0432, {total} \u043a\u043e\u043d\u0444\u0438\u0433\u043e\u0432{C.R}")
    print(f"    {C.GRN}\u041f\u0440\u043e\u0442\u043e\u043a\u043e\u043b\u044b: VLESS Reality | VMess | Trojan | SS | HY2 | TUIC | WG{C.R}")
    print(f"    {C.GRN}\u0422\u0440\u0430\u043d\u0441\u043f\u043e\u0440\u0442\u044b: tcp+reality | xhttp | ws | grpc | quic{C.R}")
    print(f"\n{C.B}{'=' * 60}{C.R}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n  {C.YEL}\u26a0 \u041f\u0440\u0435\u0440\u0432\u0430\u043d\u043e \u043f\u043e\u043b\u044c\u0437\u043e\u0432\u0430\u0442\u0435\u043b\u0435\u043c.{C.R}")
        sys.exit(0)
    except Exception as e:
        if not _quiet:
            print(f"\n  {C.RED}\u2717 \u041a\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043a\u0430\u044f \u043e\u0448\u0438\u0431\u043a\u0430: {e}{C.R}")
        sys.exit(1)
