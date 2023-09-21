import random
import re
import string

from django.db import models


class BusinessUnit(models.Model):
    apikey = models.CharField(max_length=128, blank=True, verbose_name="apikey")
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='name')
    gpt_api_key = models.CharField(max_length=300, null=True, blank=True, verbose_name='gpt api key')
    documents_list = models.TextField(blank=True, verbose_name="documents list")
    sendpulse_secret = models.CharField(max_length=128, blank=True, verbose_name="sendpulse secret")
    sendpulse_id = models.CharField(max_length=128, blank=True, verbose_name="sendpulse id")
    sendpulse_token = models.TextField(blank=True, verbose_name="sendpulse token")
    last_update_sendpulse = models.DateTimeField(auto_now=False, blank=True, null=True)
    google_creds = models.FileField(upload_to='google_creds/', null=True, verbose_name="google credentials")
    default_text = models.CharField(max_length=600, blank=True, verbose_name="default text")
    last_update_document = models.DateTimeField(auto_now=False, blank=True, null=True)

    def generate_new_apikey(self):
        key = None
        apikey_generated = False
        digits = string.digits.replace("1", "")
        letters = re.sub("[Il]", "", string.ascii_letters)
        while not apikey_generated:
            first_key = "".join([random.choice(digits) for i in range(4)])
            second_key = "".join([random.choice(letters + digits) for i in range(4)])
            key = "%s-%s" % (first_key, second_key)
            if not BusinessUnit.objects.filter(apikey=key).exists():
                apikey_generated = True
        self.apikey = key
        return key

    def save(self, *args, **kwargs):
        if not self.apikey:
            self.generate_new_apikey()
        super(BusinessUnit, self).save(*args, **kwargs)
