import io
import os

import googleapiclient.discovery as discovery
import openai
from httplib2 import Http
from langchain.chat_models import ChatOpenAI
from llama_index import GPTVectorStoreIndex, LLMPredictor, ServiceContext, SimpleDirectoryReader, \
    load_index_from_storage, StorageContext
from oauth2client.service_account import ServiceAccountCredentials

SCOPES = 'https://www.googleapis.com/auth/documents.readonly'
DISCOVERY_DOC = 'https://docs.googleapis.com/$discovery/rest?version=v1'


def get_credentials(file_url):
    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        file_url, [SCOPES, ]
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
    filename = os.path.join(documents_folder, doc['title'] + '.txt')
    if not os.path.exists(documents_folder):
        os.mkdir(documents_folder)
    with io.open(filename, 'wb') as f:
        f.write(read_structural_elements(doc_content).encode('utf-8'))
    llm_predictor = LLMPredictor(
        llm=ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    )
    service_context = ServiceContext.from_defaults(llm_predictor=llm_predictor)
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
    return response
