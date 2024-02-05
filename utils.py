from __future__ import annotations
from __future__ import annotations

import datetime
import io
import json
import os
import shutil
import time
from http.client import OK

import googleapiclient.discovery as discovery
import openai
import requests
from httplib2 import Http
from llama_index import GPTVectorStoreIndex, ServiceContext, SimpleDirectoryReader, \
    load_index_from_storage, StorageContext
from llama_index.llms import OpenAI
from llama_index.schema import Document
from oauth2client.service_account import ServiceAccountCredentials

from business_units.models import BusinessUnit
from eddy_school.settings import SEND_PULSE_URL, SMART_SENDER_URL

SEND_PULSE_AUTH = '/oauth/access_token'

SEND_PULSE_TELEGRAM_MESSAGE = '/telegram/contacts/sendText'
SEND_PULSE_TELEGRAM_RUN_BY_TRIGGER = '/telegram/flows/runByTrigger'

SEND_PULSE_VIBER_MESSAGE = '/viber/chatbots/contacts/send'
SEND_PULSE_VIBER_RUN_BY_TRIGGER = '/viber/chatbots/flows/runByTrigger'

SEND_PULSE_LIVE_CHAT_MESSAGE = '/live-chat/contacts/send'
SEND_PULSE_LIVE_CHAT_RUN_BY_TRIGGER = '/live-chat/flows/runByTrigger'

SMART_SENDER_MESSAGE = '/v1/contacts/{contactId}/send'
SMART_SENDER_RUN_BY_TRIGGER = '/v1/contacts/{contactId}/fire'

SCOPES = ['https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/drive']
DISCOVERY_DOC = 'https://docs.googleapis.com/$discovery/rest?version=v1'
DISCOVERY_DRIVE = 'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest'

REFINE_PROMPT = (
    """
    ## User Query
        {query}



    ## Context
        {reference_answer}



    ## Generated Answer
        {generated_answer}
    """
)


def get_credentials(file_url):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        file_url, SCOPES
    )
    return credentials


def read_paragraph_element(element):
    text_run = element.get('textRun')
    if not text_run:
        return ''
    return text_run.get('content')


def read_structural_elements(elements):
    text = ''
    for value in elements:
        if 'paragraph' in value:
            elements = value.get('paragraph').get('elements')
            for elem in elements:
                text += read_paragraph_element(elem)
        elif 'table' in value:
            table = value.get('table')
            for row in table.get('tableRows'):
                cells = row.get('tableCells')
                for cell in cells:
                    text += read_structural_elements(cell.get('content'))
        elif 'tableOfContents' in value:
            toc = value.get('tableOfContents')
            text += read_structural_elements(toc.get('content'))
    return text


def run_correctness_eval(
        query_str: str,
        reference_answer: str,
        generated_answer: str,
        llm: OpenAI,
        threshold: float = 0.0,
        eval_chat_template=None
):
    """Run correctness eval."""
    fmt_messages = eval_chat_template.format_messages(
        llm=llm,
        query=query_str,
        reference_answer=reference_answer,
        generated_answer=generated_answer,
    )
    chat_response = llm.chat(fmt_messages)
    raw_output = chat_response.message.content

    # Extract from response
    try:
        score_str, reasoning_str = raw_output.split("\n", 1)
        score = float(score_str)
        reasoning = reasoning_str.lstrip("\n")

        return {"passing": score >= threshold, "score": score, "reason": reasoning}
    except:
        try:
            score = float(raw_output)
            reasoning = reasoning_str.lstrip("\n")

            return {"passing": score >= threshold, "score": score, "reason": reasoning}
        except:
            score = raw_output.split(".")[0]

            return {"score": score}


def make_query(query_text, document_id, documents_folder, index_name, openai_key, file_url):
    openai.api_key = openai_key
    os.environ["OPENAI_API_KEY"] = openai.api_key
    credentials = get_credentials(file_url)
    http = credentials.authorize(Http())
    docs_service = discovery.build(
        'docs', 'v1', http=http, discoveryServiceUrl=DISCOVERY_DOC)
    doc = docs_service.documents().get(documentId=document_id).execute()
    doc_content = doc.get('body').get('content')

    drive = discovery.build("drive", "v3", http=http, discoveryServiceUrl=DISCOVERY_DRIVE)

    last_modified = datetime.datetime.strptime(
        drive.files().get(fileId=document_id, fields='*').execute()['modifiedTime'], '%Y-%m-%dT%H:%M:%S.%fZ')

    business_unit = BusinessUnit.objects.filter(apikey=documents_folder.split('documents-')[1]).first()

    filename = os.path.join(documents_folder, doc['title'] + '.txt')

    if not os.path.exists(documents_folder) or not business_unit.last_update_document:
        try:
            os.mkdir(documents_folder)
        except:
            pass
        business_unit.last_update_document = last_modified
        business_unit.save()
    elif business_unit.last_update_document.strftime('%Y-%m-%dT%H:%M:%S.%fZ') < last_modified.strftime(
            '%Y-%m-%dT%H:%M:%S.%fZ'):
        if os.path.exists(documents_folder):
            shutil.rmtree(documents_folder)
        if os.path.exists(index_name):
            shutil.rmtree(index_name)

        os.mkdir(documents_folder)
        business_unit.last_update_document = last_modified
        business_unit.save()
    with io.open(filename, 'wb') as f:
        f.write(read_structural_elements(doc_content).encode('utf-8'))
        temperature = business_unit.temperature
    if business_unit.max_tokens:
        llm = OpenAI(model=business_unit.gpt_model, temperature=temperature,
                     max_tokens=business_unit.max_tokens)
    else:
        llm = OpenAI(model=business_unit.gpt_model, temperature=temperature)

    service_context = ServiceContext.from_defaults(llm=llm,
                                                   system_prompt=business_unit.system_prompt)
    if os.path.exists(index_name):
        index = load_index_from_storage(
            StorageContext.from_defaults(persist_dir=index_name),
            service_context=service_context,
        )
    else:
        documents = SimpleDirectoryReader(documents_folder).load_data()
        index = GPTVectorStoreIndex.from_documents(
            documents, service_context=service_context
        )
        index.storage_context.persist(persist_dir=index_name)

    query_engine = index.as_query_engine(similarity_top_k=1)
    response = query_engine.query(query_text)

    context = []

    for context_info in response.source_nodes:
        context.append(Document(text=context_info.node.get_content()).text)

    context = f"{context[0]}"

    # eval_chat_template = ChatPromptTemplate(
    #     message_templates=[
    #         ChatMessage(role=MessageRole.SYSTEM, content=business_unit.eval_prompt),
    #         ChatMessage(role=MessageRole.USER, content=REFINE_PROMPT),
    #     ]
    # )
    # llm = OpenAI(model=business_unit.gpt_model)

    # eval_result = run_correctness_eval(
    #     query_str=query_text, reference_answer=context, generated_answer=response.response,
    #     eval_chat_template=eval_chat_template, llm=llm, threshold=4.0
    # )

    return {"response": response.response, "eval_result": 5,
            "llm_context": context}


def translate_to_ukrainian(text):
    return text
    # translator = Translator()
    #
    # try:
    #     source_lang = translator.detect(text).lang
    #
    #     if source_lang == 'en':
    #         translation = translator.translate(text, src='en', dest='uk').text
    #         return translation
    #     else:
    #         return text
    # except:
    #     return text


def smart_sender_flow(request_type, business_units, contact_id=None, response=None):
    headers = {"Authorization": f"Bearer {business_units.smart_sender_token}"}

    if request_type == "send_message":
        r = requests.post(f'{SMART_SENDER_URL}{SMART_SENDER_MESSAGE.format(contactId=contact_id)}', headers=headers,
                          data={
                              "content": response,
                              "type": "text",
                              "watermark": int(time.time())
                          })
        return r
    elif request_type == "word_trigger":
        r = requests.post(f'{SMART_SENDER_URL}{SMART_SENDER_RUN_BY_TRIGGER.format(contactId=contact_id)}',
                          headers=headers,
                          data={
                              "name": business_units.default_text
                          })
        return r


def send_pulse_flow(request_type, business_units, contact_id=None, source_type=None, **kwargs):
    headers = {"Authorization": f"Bearer {business_units.sendpulse_token}"}

    if request_type == "auth":
        datetime_now = datetime.datetime.now(datetime.timezone.utc)

        data = {
            "grant_type": "client_credentials",
            "client_id": business_units.sendpulse_id,
            "client_secret": business_units.sendpulse_secret
        }
        sendpulse_auth = json.loads(requests.post(f'{SEND_PULSE_URL}{SEND_PULSE_AUTH}', data=data).text)

        business_units.sendpulse_token = sendpulse_auth.get('access_token', None)
        business_units.last_update_sendpulse = datetime_now
        business_units.save()
        return OK

    elif request_type == "word_trigger":
        send_pulse_url = {
            "telegram": SEND_PULSE_TELEGRAM_RUN_BY_TRIGGER,
            "viber": SEND_PULSE_VIBER_RUN_BY_TRIGGER,
            "live_chat": SEND_PULSE_LIVE_CHAT_RUN_BY_TRIGGER,
        }[source_type]

        request_data = {
            "contact_id": contact_id,
            "trigger_keyword": business_units.default_text,
        }

        r = requests.post(
            f"{SEND_PULSE_URL}{send_pulse_url}", headers=headers, data=request_data
        )

        return r

    elif request_type == "send_message":
        part = kwargs.get("part", None)

        if part and source_type == "telegram":
            r = requests.post(f'{SEND_PULSE_URL}{SEND_PULSE_TELEGRAM_MESSAGE}', headers=headers, data={
                "contact_id": contact_id,
                "text": part
            })
            return r

        elif part and source_type == "viber":
            r = requests.post(f'{SEND_PULSE_URL}{SEND_PULSE_VIBER_MESSAGE}', headers=headers, json={
                "contact_id": contact_id,
                "messages": [
                    {
                        "type": "text",
                        "text": {
                            "text": part
                        }
                    }
                ]
            })
            return r

        elif part and source_type == "live_chat":
            r = requests.post(f'{SEND_PULSE_URL}{SEND_PULSE_LIVE_CHAT_MESSAGE}', headers=headers, json={
                "contact_id": contact_id,
                "messages": [
                    {
                        "type": "text",
                        "text": {
                            "text": part
                        }
                    }
                ]
            })
            return r


def gpt_assistant_query(query_text, business_unit, openai_key):
    openai.api_key = openai_key
    os.environ["OPENAI_API_KEY"] = openai.api_key

    client = openai.OpenAI()
    thread = client.beta.threads.create()

    message = client.beta.threads.messages.create(
        thread_id=thread.id,
        role="user",
        content=query_text
    )

    run = client.beta.threads.runs.create(
        thread_id=thread.id,
        assistant_id=business_unit.gpt_assistant_id
    )

    while True:
        time.sleep(5)

        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread.id,
            run_id=run.id
        )

        if run_status.status == 'completed':
            messages = client.beta.threads.messages.list(
                thread_id=thread.id
            )

            for msg in messages.data:
                role = msg.role
                content = msg.content[0].text.value
                if role.capitalize() == 'Assistant':
                    return {"response": content, "eval_result": 5,
                            "llm_context": "None, it's GPT assistant mode!"}

            break
