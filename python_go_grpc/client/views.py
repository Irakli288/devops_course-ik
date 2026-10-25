import logging

from django.shortcuts import render
from django.http import HttpResponse

from .api.client import Certs
from .api.client import Client

logger = logging.getLogger(__name__)

# 🎲 Game Die
# ⚀ ⚁ ⚂ ⚃ ⚄ ⚅ can be shown in text using the range U+2680 to U+2685
ICONS = ["?", "⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]

GRPC_ADDR = "127.0.0.1:8443"   # Go-сервер напрямую (mTLS)
NGINX_ADDR = "127.0.0.1:9448"  # Go-сервер через nginx (mTLS)


def certs():
    return Certs('certs/ca.pem', 'certs/client.pem', 'certs/client-key.pem')


def index(request):
    value_a, value_b = 0, 0
    if request.method == "POST":
        crt = certs()
        try:
            value_a = Client(GRPC_ADDR, crt).roll_die()
        except Exception as e:
            logger.exception(e)
        try:
            value_b = Client(NGINX_ADDR, crt).roll_die()
        except Exception as e:
            logger.exception(e)

    ctx = {
        "icon_a": ICONS[value_a],
        "icon_b": ICONS[value_b],
        "sign": "=" if value_a == value_b else "<" if value_a < value_b else ">",
    }
    return render(request, "index.html", context=ctx)


def grpc(request):
    value = 0
    try:
        value = Client(GRPC_ADDR, certs()).roll_die()
    except Exception as e:
        logger.exception(e)
    return HttpResponse('Value: ' + ICONS[value])


def nginx(request):
    value = 0
    try:
        value = Client(NGINX_ADDR, certs()).roll_die()
    except Exception as e:
        logger.exception(e)
    return HttpResponse('Value: ' + ICONS[value])
