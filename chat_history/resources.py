from import_export import resources

from .models import ChatHistory


class ChatHistoryResource(resources.ModelResource):
    class Meta:
        model = ChatHistory
