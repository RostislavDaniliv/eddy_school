import os
import random
import re
import string

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from eddy_school import settings


class BusinessUnit(models.Model):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_NEW = "gpt-3.5-turbo-1106"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-1106-preview"
    GPT_4_O = "gpt-4o"

    STRICT_MODE = 1
    MANAGER_FLOW = 2
    SOFT_MODE = 3

    SEND_PULSE = 1
    SMART_SENDER = 2

    LLM_MODE = 1
    GPT_ASSISTANT = 2

    BOT_MODE = (
        (STRICT_MODE, "Strict mode"),
        (MANAGER_FLOW, "Manager flow"),
        (SOFT_MODE, "Soft mode"),
    )

    MODEL_GPT = (
        (GPT_3_5_TURBO, "Gpt 3.5 old turbo"),
        (GPT_3_5_TURBO_NEW, "Gpt 3.5 new turbo"),
        (GPT_4, "Gpt 4"),
        (GPT_4_TURBO, "Gpt 4 preview (Turbo)"),
        (GPT_4_O, "Gpt 4 Omni"),
    )

    SENDER = (
        (SEND_PULSE, "Sendpulse"),
        (SMART_SENDER, "Smartsendereu")
    )

    SCRIPT_MODE = (
        (LLM_MODE, "LlamaIndex"),
        (GPT_ASSISTANT, "GPT Assist")
    )

    apikey = models.CharField(max_length=128, blank=True, verbose_name="apikey")
    name = models.CharField(max_length=100, null=True, blank=True, verbose_name='name')
    gpt_api_key = models.CharField(max_length=300, null=True, blank=True, verbose_name='gpt api key')
    documents_list = models.TextField(blank=True, verbose_name="documents list")
    sendpulse_secret = models.CharField(max_length=128, blank=True, verbose_name="sendpulse secret")
    sendpulse_id = models.CharField(max_length=128, blank=True, verbose_name="sendpulse id")
    sendpulse_token = models.TextField(blank=True, verbose_name="sendpulse token")
    smart_sender_token = models.TextField(blank=True, verbose_name="Smartsender token")
    last_update_sendpulse = models.DateTimeField(auto_now=False, blank=True, null=True)
    last_used_documents_list = models.TextField(blank=True, verbose_name="last used documents list")
    google_creds = models.FileField(upload_to='google_creds/',
                                    default='media/google_creds/default_key.json', null=True,
                                    verbose_name="google credentials")
    default_text = models.CharField(max_length=600, blank=True, verbose_name="default text")
    panic_text = models.CharField(max_length=600, blank=True, verbose_name="panic text")
    last_update_document = models.DateTimeField(auto_now=False, blank=True, null=True)
    temperature = models.FloatField(default=0, verbose_name="temperature")
    max_tokens = models.IntegerField(default=0, verbose_name="max tokens")
    chunk_size = models.IntegerField(default=0, verbose_name="chunk size")
    chunk_overlap = models.IntegerField(default=0, verbose_name="chunk overlap")
    similarity_top_k = models.IntegerField(default=0, verbose_name="similarity top k")
    chunk_splitter = models.CharField(max_length=10, null=True, blank=True, verbose_name='chunk splitter')
    bot_mode = models.PositiveIntegerField(choices=BOT_MODE, default=STRICT_MODE,
                                           verbose_name='bot mode')
    gpt_model = models.CharField(max_length=100, choices=MODEL_GPT, default=GPT_3_5_TURBO,
                                 verbose_name='GPT model')
    eval_prompt = models.TextField(null=True, blank=True, verbose_name="eval promt")
    system_prompt = models.TextField(null=True, blank=True, verbose_name="system prompt")
    eval_score = models.FloatField(default=3, verbose_name="eval score (max 5)")
    sending_service = models.PositiveIntegerField(choices=SENDER, default=SEND_PULSE,
                                                  verbose_name='Sender service')
    script_mode = models.PositiveIntegerField(choices=SCRIPT_MODE, default=LLM_MODE,
                                              verbose_name='Script mode')
    gpt_assistant_id = models.CharField(max_length=128, blank=True, verbose_name="GPT assistant id")
    is_active = models.BooleanField(default=True)
    similarity_simple_q = models.FloatField(default=0.79, verbose_name="similarity simple question",
                                            help_text="Визначає ступінь подібності між заданим та збереженим "
                                                      "питанням. Значення 0.96 для ідентичного питання, "
                                                      "зміни в тексті зменшують подібність до 0.79-0.85. При сильному "
                                                      "перефразуванні це 0.66",
                                            validators=[MinValueValidator(0.50), MaxValueValidator(0.94)]
                                            )
    is_trial_user_limits = models.BooleanField(
        default=False, verbose_name="Limits for trial users",
        help_text="Активуйте, щоб застосувати обмеження використання для тестових користувачів цього модуля."
    )
    requests_count_limit = models.IntegerField(
        default=0, verbose_name="Максимальна кількість запитів для тестового користувача"
    )
    file_size_limit = models.IntegerField(
        default=0, verbose_name="Максимальний розмір файлу для тестового користувача"
    )
    token_used = models.IntegerField(
        default=0, verbose_name="Максимальна кількість токенів для тестового користувача"
    )
    usage_limit_message = models.CharField(
        max_length=500,
        default="Ви перевищили встановлений ліміт використання наших ресурсів. Будь ласка, зверніться до нашої служби"
                " підтримки для отримання додаткової інформації.", verbose_name="usage limit message"
    )

    def __str__(self):
        return f"{self.name} - {self.apikey}"

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


class Document(models.Model):
    name = models.CharField(max_length=100, blank=True, null=True)
    document_id = models.CharField(max_length=100, null=True, blank=True)
    file = models.FileField(upload_to='documents/', blank=True, null=True)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.document_id}"


class SimpleQuestions(models.Model):
    business_unit = models.ForeignKey(BusinessUnit, related_name='sqs', on_delete=models.CASCADE)
    question = models.TextField()
    answer = models.TextField()

    def __str__(self):
        return self.question

    def get_questions(self):
        return self.question.split('|')


class TestUser(models.Model):
    contact_id = models.CharField(max_length=200)
    file_hash_sum = models.CharField(max_length=500, null=True, blank=True)
    request_count = models.IntegerField(null=False, blank=False, default=0)
    file_size = models.FloatField(null=False, blank=False, default=0)
    token_used = models.IntegerField(null=False, blank=False, default=0)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="created at")
