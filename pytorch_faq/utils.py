import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

from business_units.models import BusinessUnit


def load_model_and_tokenizer(model_name='cross-encoder/nli-distilroberta-base'):
    tokenizer_p = AutoTokenizer.from_pretrained(model_name)
    model_p = AutoModelForSequenceClassification.from_pretrained(model_name)
    return model_p, tokenizer_p


def get_similarity(u_question, sample_question, model_p, tokenizer_p):
    inputs = tokenizer_p(u_question, sample_question, return_tensors="pt", truncation=True)
    with torch.no_grad():
        outputs = model_p(**inputs)
    similarity_p = torch.nn.functional.softmax(outputs.logits, dim=1)[0][1].item()
    return similarity_p


def find_closest_answer(bu_id, u_question, similarity_threshold=0.7):
    model_p, tokenizer_p = load_model_and_tokenizer()
    business_unit = BusinessUnit.objects.get(id=bu_id)
    faqs = business_unit.sqs.all()
    best_similarity = 0
    best_answer = None

    for faq in faqs:
        questions = faq.get_questions()
        for question in questions:
            similarity = get_similarity(u_question, question, model_p, tokenizer_p)
            if similarity > best_similarity:
                best_similarity = similarity
                best_answer = faq.answer

    if best_similarity >= similarity_threshold:
        print(f"ANSWER: {best_answer} \n POINTS: {best_similarity}")
        return best_answer
    else:
        print(f"ONLY POINTS: {best_similarity}")
        return False
