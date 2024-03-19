import datetime

from django.http import HttpResponse, JsonResponse
from rest_framework.views import APIView

from business_units.models import BusinessUnit
from utils import make_query, translate_to_ukrainian, send_pulse_flow, gpt_assistant_query, smart_sender_flow


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
                - "source_type: тип зв'язку.
                - "document_id: ід документу (Для лендінг пейджа).

            Response: 200
        """

        query_text = request.data.get('query_text', None)
        apikey = request.data.get('apikey', None)
        contact_id = request.data.get('contact_id', None)
        source_type = request.data.get('source_type', "telegram")
        llm_context = request.data.get('llm_context', None)
        document_id = request.data.get('document_id', None)
        resave_documents = True

        if not apikey:
            return HttpResponse("Apikey parameters are missing", status=401)

        business_units = BusinessUnit.objects.filter(apikey=apikey).first()

        if not business_units:
            return HttpResponse("business_units doesn't exist", status=400)

        datetime_now = datetime.datetime.now(datetime.timezone.utc)

        if (not business_units.sendpulse_token or
                datetime_now - business_units.last_update_sendpulse > datetime.timedelta(minutes=50)):
            send_pulse_flow(request_type="auth", business_units=business_units)

        index_name = f"./saved_index-{business_units.apikey}"
        documents_folder = f"./documents-{business_units.apikey}"
        if not document_id:
            document_id = business_units.documents_list.split(" ")[0]
            resave_documents = False
        openai_key = business_units.gpt_api_key
        credentials_file_name = f"eddy_school/media/google_creds/{business_units.google_creds.url.split('/')[3]}"

        if business_units.script_mode == BusinessUnit.LLM_MODE:
            response_q = make_query(
                query_text,
                document_id,
                documents_folder,
                index_name,
                openai_key,
                credentials_file_name,
                resave_documents
            )
        else:
            response_q = gpt_assistant_query(query_text, business_units, openai_key)

        if business_units.bot_mode == BusinessUnit.STRICT_MODE:
            if float(response_q['eval_result']) < business_units.eval_score:
                response = business_units.default_text
            else:
                response = translate_to_ukrainian(response_q['response'])
        elif business_units.bot_mode == BusinessUnit.MANAGER_FLOW:
            if response_q['response'] == business_units.default_text:
                if business_units.sending_service == BusinessUnit.SEND_PULSE:
                    r = send_pulse_flow(
                        request_type="word_trigger",
                        business_units=business_units,
                        contact_id=contact_id,
                        source_type=source_type
                    )
                else:
                    r = smart_sender_flow(
                        request_type="word_trigger",
                        business_units=business_units,
                        contact_id=contact_id,
                    )

                return JsonResponse({"response": response_q, "sendpulse_cont": r.content.decode('utf-8')})
            else:
                response = translate_to_ukrainian(response_q['response'])
        else:
            if response_q['response'].startswith("I'm sorry"):
                response = business_units.default_text
            else:
                response = translate_to_ukrainian(response_q['response'])

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

        if business_units.sending_service == BusinessUnit.SEND_PULSE:
            for i, part in enumerate(text_parts):
                r = send_pulse_flow(
                    request_type="send_message",
                    business_units=business_units,
                    contact_id=contact_id,
                    part=part,
                    source_type=source_type
                )
                sendpulse_response.append(r.content.decode('utf-8'))

            return JsonResponse({"user_question": query_text, "response": response_q,
                                     "sendpulse_cont": sendpulse_response})
        else:
            r = smart_sender_flow(
                request_type="send_message",
                business_units=business_units,
                contact_id=contact_id,
                response=response
            )
            return JsonResponse({"user_question": query_text, "response": response_q['response'],
                                 "smart_sender": r.content.decode('utf-8')})
