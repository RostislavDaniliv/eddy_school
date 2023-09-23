import datetime
import json

import requests
from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView

from business_units.models import BusinessUnit
from eddy_school.settings import SEND_PULSE_URL
from utils import make_query

SEND_PULSE_AUTH = '/oauth/access_token'
SEND_PULSE_TELEGRAM_MESSAGE = '/telegram/contacts/sendText'


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

        if response['eval_result'] == "NO":
            response = business_units.default_text
        else:
            response = response['response']

        headers = {"Authorization": f"Bearer {business_units.sendpulse_token}"}
        requests.post(f'{SEND_PULSE_URL}{SEND_PULSE_TELEGRAM_MESSAGE}', headers=headers, data={
            "contact_id": contact_id,
            "text": response
        })

        return JsonResponse({"response": response})
