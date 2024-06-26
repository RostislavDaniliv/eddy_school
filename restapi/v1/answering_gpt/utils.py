import datetime

from django.http import HttpResponse

from business_units.models import BusinessUnit, Document
from utils import (
    make_query, translate_to_ukrainian, send_pulse_flow,
    gpt_assistant_query, smart_sender_flow, split_text_into_parts
)


def update_send_pulse_if_needed(business_unit):
    datetime_now = datetime.datetime.now(datetime.timezone.utc)
    if (not business_unit.sendpulse_token or
            datetime_now - business_unit.last_update_sendpulse > datetime.timedelta(minutes=50)):
        send_pulse_flow(request_type="auth", business_units=business_unit)


def get_business_unit(apikey):
    business_unit = BusinessUnit.objects.filter(apikey=apikey).first()
    if not business_unit:
        return None, HttpResponse("business unit doesn't exist", status=400)
    if not business_unit.is_active:
        return None, HttpResponse("Business unit isn't active", status=400)
    return business_unit, None


def get_query_params(request):
    required_params = ['query_text', 'apikey', 'contact_id', 'source_type']
    params = {param: request.data.get(param, None) for param in required_params}
    params['llm_context'] = request.data.get('llm_context', None)
    params['document_id'] = [request.data.get('document_id'), ] if request.data.get('document_id', None) else None

    if not params['apikey']:
        return {'error': HttpResponse("Apikey parameters are missing", status=401)}
    return params


def generate_response(query_text, business_unit, document_id, llm_context):
    if business_unit.script_mode == BusinessUnit.LLM_MODE:
        resave_documents = True
        if not document_id:
            document_id = list(Document.objects.filter(business_unit=business_unit).values_list('document_id', flat=True))
            resave_documents = False
        return make_query(
            query_text, document_id, f"./documents-{business_unit.apikey}",
            f"./saved_index-{business_unit.apikey}", business_unit.gpt_api_key,
            f"eddy_school/media/google_creds/{business_unit.google_creds.url.split('/')[3]}",
            resave_documents
        )
    else:
        return gpt_assistant_query(query_text, business_unit, business_unit.gpt_api_key)


def determine_response_text(business_unit, response_q):
    if business_unit.bot_mode == BusinessUnit.STRICT_MODE:
        return business_unit.default_text if float(response_q['eval_result']) < business_unit.eval_score \
            else translate_to_ukrainian(response_q['response'])
    elif response_q['response'].startswith("I'm sorry"):
        return business_unit.default_text
    return translate_to_ukrainian(response_q['response'])


def send_response(business_unit, user_q, text_parts, contact_id, source_type, response_text, llm_context):
    if business_unit.sending_service == BusinessUnit.SEND_PULSE:
        sendpulse_response = [
            send_pulse_flow(request_type="send_message", business_units=business_unit, contact_id=contact_id,
                            part=part, source_type=source_type).content.decode('utf-8')
            for part in text_parts
        ]
        return {"user_question": user_q, "response": response_text, "chunks": llm_context,
                "sendpulse_cont": sendpulse_response}
    else:
        r = smart_sender_flow(request_type="send_message", business_units=business_unit, contact_id=contact_id,
                              response=response_text)
        return {"user_question": user_q, "response": response_text,
                "smart_sender": r.content.decode('utf-8')}


def process_response(business_unit, user_q, response_q, contact_id, source_type):
    response = determine_response_text(business_unit, response_q)
    text_parts = split_text_into_parts(response)
    return send_response(business_unit, user_q, text_parts, contact_id, source_type, response_q['response'],
                         response_q['llm_context'])
