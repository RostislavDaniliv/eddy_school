import datetime
import io
import os
import shutil

import googleapiclient.discovery as discovery
import openai
from httplib2 import Http
from langchain.chat_models import ChatOpenAI
from llama_index import GPTVectorStoreIndex, LLMPredictor, ServiceContext, SimpleDirectoryReader, \
    load_index_from_storage, StorageContext
from llama_index.evaluation import ResponseEvaluator
from oauth2client.service_account import ServiceAccountCredentials

from business_units.models import BusinessUnit

SCOPES = ['https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/drive']
DISCOVERY_DOC = 'https://docs.googleapis.com/$discovery/rest?version=v1'
DISCOVERY_DRIVE = 'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest'


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
    llm_predictor = LLMPredictor(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=1)
    )
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
    evaluator = ResponseEvaluator(service_context=service_context)
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

    query_engine = index.as_query_engine()
    response = query_engine.query(query_text)
    eval_result = evaluator.evaluate(response)
    return {"response": response.response, "eval_result": eval_result}
