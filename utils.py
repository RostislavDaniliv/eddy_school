from __future__ import annotations
from __future__ import annotations

import datetime
import io
import os
import shutil
from typing import List, Optional

import googleapiclient.discovery as discovery
import openai
from googletrans import Translator
from httplib2 import Http
from langchain.chat_models import ChatOpenAI
from llama_index import GPTVectorStoreIndex, LLMPredictor, ServiceContext, SimpleDirectoryReader, \
    load_index_from_storage, StorageContext
from llama_index.evaluation.base import DEFAULT_EVAL_PROMPT, DEFAULT_REFINE_PROMPT
from llama_index.indices.list.base import SummaryIndex
from llama_index.prompts.base import PromptTemplate
from llama_index.response.schema import Response
from llama_index.schema import Document
from oauth2client.service_account import ServiceAccountCredentials

from business_units.models import BusinessUnit

SCOPES = ['https://www.googleapis.com/auth/documents.readonly', 'https://www.googleapis.com/auth/drive']
DISCOVERY_DOC = 'https://docs.googleapis.com/$discovery/rest?version=v1'
DISCOVERY_DRIVE = 'https://www.googleapis.com/discovery/v1/apis/drive/v3/rest'

REFINE_PROMPT = (
    """
    ## User Query
        {query}

    ## Reference Answer
        {reference_answer}

    ## Generated Answer
        {generated_answer}
    """
)


class ResponseEvaluator:
    """Evaluate based on response from indices.

    NOTE: this is a beta feature, subject to change!

    Args:
        service_context (Optional[ServiceContext]): ServiceContext object

    """

    def __init__(
            self,
            service_context: Optional[ServiceContext] = None,
            eval_prompt_tmpl: Optional[PromptTemplate] = None,
            refine_prompt_tmpl: Optional[PromptTemplate] = None,
            raise_error: bool = False,
    ) -> None:
        """Init params."""
        self.service_context = service_context or ServiceContext.from_defaults()
        self.eval_prompt_tmpl = eval_prompt_tmpl or PromptTemplate(DEFAULT_EVAL_PROMPT)
        self.refine_prompt_tmpl = refine_prompt_tmpl or PromptTemplate(
            DEFAULT_REFINE_PROMPT
        )

        self.raise_error = raise_error

    def get_context(self, response: Response) -> List[Document]:
        """Get context information from given Response object using source nodes.

        Args:
            response (Response): Response object from an index based on the query.

        Returns:
            List of Documents of source nodes information as context information.
        """

        context = []

        for context_info in response.source_nodes:
            context.append(Document(text=context_info.node.get_content()))

        return context

    def evaluate(self, response: Response) -> str:
        """Evaluate the response from an index.

        Args:
            query: Query for which response is generated from index.
            response: Response object from an index based on the query.
        """
        answer = str(response)

        context = self.get_context(response)
        index = SummaryIndex.from_documents(
            context, service_context=self.service_context
        )

        query_engine = index.as_query_engine(
            text_qa_template=self.eval_prompt_tmpl,
            refine_template=self.refine_prompt_tmpl,
        )
        response_obj = query_engine.query(answer)

        raw_response_txt = str(response_obj)

        return raw_response_txt.split("\n")[0]


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
    temperature = business_unit.temperature
    if business_unit.max_tokens:
        llm_predictor = LLMPredictor(
            llm=ChatOpenAI(model_name=business_unit.gpt_model, temperature=temperature, max_tokens=business_unit.max_tokens)
        )
    else:
        llm_predictor = LLMPredictor(
            llm=ChatOpenAI(model_name=business_unit.gpt_model, temperature=temperature)
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
    user_message = REFINE_PROMPT.format(
        query=query_text,
        reference_answer=index,
        generated_answer=response
    )
    eval_promt = business_unit.eval_prompt.format(
        answer=response,
        query_str=query_text
    )
    evaluator = ResponseEvaluator(
        service_context=service_context,
        eval_prompt_tmpl=PromptTemplate(eval_promt),
        refine_prompt_tmpl=PromptTemplate(user_message)
    )
    eval_result = evaluator.evaluate(response)
    return {"response": response.response, "eval_result": eval_result}


def translate_to_ukrainian(text):
    translator = Translator()

    source_lang = translator.detect(text).lang

    if source_lang == 'en':
        translation = translator.translate(text, src='en', dest='uk').text
        return translation
    else:
        return text
