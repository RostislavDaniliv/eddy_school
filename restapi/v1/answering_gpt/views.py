from django.http import JsonResponse
from rest_framework.views import APIView

from restapi.v1.answering_gpt.utils import get_query_params, get_business_unit, update_send_pulse_if_needed, \
    generate_response, process_response
from restapi.v1.document.utils import create_chat_history


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

        query_params = get_query_params(request)
        if query_params.get('error', None):
            return query_params['error']

        business_unit, response = get_business_unit(query_params['apikey'])
        if response:
            return response

        update_send_pulse_if_needed(business_unit)
        response_q = generate_response(query_text=query_params['query_text'],
                                       business_unit=business_unit,
                                       document_id=query_params['document_id'],
                                       llm_context=query_params['llm_context'])
        final_response = process_response(business_unit=business_unit,
                                          response_q=response_q,
                                          contact_id=query_params['contact_id'],
                                          source_type=query_params['source_type'])
        create_chat_history(
            business_unit=business_unit,
            username=request.data.get('username'),
            user_id=request.data.get('user_id'),
            user_question=query_params['query_text'],
            system_answer=response_q['response']
        )

        return JsonResponse(final_response)
