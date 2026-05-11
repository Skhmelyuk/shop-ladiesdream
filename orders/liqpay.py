import base64
import hashlib
import json
from django.conf import settings

class LiqPay:
    """
    Клас для взаємодії з API LiqPay (генерація data та signature)
    """
    def __init__(self, public_key, private_key):
        self.public_key = public_key
        self.private_key = private_key

    def _generate_signature(self, data):
        """
        Генерує підпис (signature) для LiqPay
        """
        sha1_string = self.private_key + data + self.private_key
        sha1_hash = hashlib.sha1(sha1_string.encode('utf-8')).digest()
        return base64.b64encode(sha1_hash).decode('utf-8')

    def cpay_params(self, params):
        """
        Готує параметри для відправки форми на LiqPay
        """

        full_params = {
            'public_key': self.public_key,
            'version': 3,
            'action': 'pay',
            'currency': 'UAH',
            **params
        }

        data = base64.b64encode(json.dumps(full_params).encode('utf-8')).decode('utf-8')
        signature = self._generate_signature(data)
        return {
            'data': data,
            'signature': signature,
            'send_url': settings.LIQPAY_SEND_URL,
        }

liqpay_client = LiqPay(settings.LIQPAY_PUBLIC_KEY, settings.LIQPAY_PRIVATE_KEY)