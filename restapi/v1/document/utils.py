from chat_history.models import ChatHistory


def create_chat_history(business_unit, username, user_id, user_question, system_answer):
    ChatHistory.objects.create(
        business_unit=business_unit,
        username=username,
        user_id=user_id,
        user_question=user_question,
        system_answer=system_answer
    )
