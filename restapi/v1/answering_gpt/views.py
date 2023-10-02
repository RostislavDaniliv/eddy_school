import datetime
import json

import requests
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView

from business_units.models import BusinessUnit
from eddy_school.settings import SEND_PULSE_URL
from utils import make_query, translate_to_ukrainian

SEND_PULSE_AUTH = '/oauth/access_token'
SEND_PULSE_TELEGRAM_MESSAGE = '/telegram/contacts/sendText'
SEND_PULSE_TELEGRAM_RUN_BY_TRIGGER = '/telegram/flows/runByTrigger'


class GPTAnswerView(APIView):
    authentication_classes = []

    def post(self, request):
        """
        Description.

            URL: /api/1.0/answering_gpt/

            Parameters:
                - "query_text": текст запитання від користувача.
                - "apikey": apikey бізнес одиниці (бота).
                - "contact_id": ід клієнта.

            Response: 200
        """

        query_text = request.data.get('query_text', None)
        apikey = request.data.get('apikey', None)
        contact_id = request.data.get('contact_id', '650346d4440c5d675704d7c6')

        if not apikey:
            return HttpResponse("Apikey parameters are missing", status=401)

        business_units = BusinessUnit.objects.filter(apikey=apikey).first()

        if not business_units:
            return HttpResponse("business_units doesn't exist", status=400)

        datetime_now = datetime.datetime.now(datetime.timezone.utc)

        if (not business_units.sendpulse_token or
                datetime_now - business_units.last_update_sendpulse > datetime.timedelta(minutes=50)):
            data = {
                "grant_type": "client_credentials",
                "client_id": business_units.sendpulse_id,
                "client_secret": business_units.sendpulse_secret
            }
            sendpulse_auth = json.loads(requests.post(f'{SEND_PULSE_URL}{SEND_PULSE_AUTH}', data=data).text)

            business_units.sendpulse_token = sendpulse_auth.get('access_token', None)
            business_units.last_update_sendpulse = datetime_now
            business_units.save()

        index_name = f"./saved_index-{business_units.apikey}"
        documents_folder = f"./documents-{business_units.apikey}"
        documents_ids = business_units.documents_list.split(" ")[0]
        openai_key = business_units.gpt_api_key
        credentials_file_name = f"eddy_school/media/google_creds/{business_units.google_creds.url.split('/')[3]}"

        response = make_query(
            query_text,
            documents_ids,
            documents_folder,
            index_name,
            openai_key,
            credentials_file_name
        )

        headers = {"Authorization": f"Bearer {business_units.sendpulse_token}"}

        if business_units.bot_mode == BusinessUnit.STRICT_MODE:
            if response['eval_result'] == "NO":
                response = business_units.default_text
            else:
                response = response['response']
        elif business_units.bot_mode == BusinessUnit.MANAGER_FLOW:
            if response['eval_result'] == "NO":
                r = requests.post(f'{SEND_PULSE_URL}{SEND_PULSE_TELEGRAM_RUN_BY_TRIGGER}', headers=headers, data={
                    "contact_id": contact_id,
                    "trigger_keyword": business_units.default_text,
                })

                return JsonResponse({"response": response, "sendpulse_cont": r.content.decode('utf-8')})
        else:
            if response['response'].startswith("I'm sorry"):
                response = business_units.default_text
            else:
                response = response['response']

        text_parts = []
        current_part = ""
        words = response.split()

        for word in words:
            if len(current_part) + len(word) + 1 <= 512:
                if current_part:
                    current_part += " "
                current_part += word
            else:
                text_parts.append(current_part)
                current_part = word

        if current_part:
            text_parts.append(current_part)

        sendpulse_response = []

        response = translate_to_ukrainian(response)

        for i, part in enumerate(text_parts):
            r = requests.post(f'{SEND_PULSE_URL}{SEND_PULSE_TELEGRAM_MESSAGE}', headers=headers, data={
                "contact_id": contact_id,
                "text": part
            })
            sendpulse_response.append(r.content.decode('utf-8'))

        return JsonResponse({"response": response, "sendpulse_cont": sendpulse_response})
