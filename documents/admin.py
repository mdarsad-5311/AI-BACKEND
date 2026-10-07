from django.contrib import admin
from documents.models import Document, Clause, Conversation, ChatMessage


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'user', 'document_type', 'status', 'page_count', 'created_at')
    list_filter = ('document_type', 'status')
    search_fields = ('title', 'id', 'file_name', 'user__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(Clause)
class ClauseAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'document', 'section_number', 'page_number', 'category')
    list_filter = ('category', 'page_number')
    search_fields = ('title', 'snippet', 'document__id')


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'document', 'user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('title', 'document__id', 'user__username')


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'created_at')
    list_filter = ('role', 'created_at')
    search_fields = ('content', 'conversation__id')

