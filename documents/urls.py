from django.urls import path
from documents.views import (
    DocumentListCreateView,
    DocumentDetailView,
    DocumentExtractTextView,
    DocumentAnalyzeView,
    DocumentClausesListView,
    ClauseDetailView,
    DocumentConversationListCreateView,
    ConversationDetailView,
    ConversationMessageCreateView,
)

urlpatterns = [
    path('documents/', DocumentListCreateView.as_view(), name='document-list-create'),
    path('documents/<str:pk>/', DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<str:pk>/extract/', DocumentExtractTextView.as_view(), name='document-extract-text'),
    path('documents/<str:pk>/analyze/', DocumentAnalyzeView.as_view(), name='document-analyze'),
    path('documents/<str:pk>/clauses/', DocumentClausesListView.as_view(), name='document-clauses-list'),
    path('clauses/<str:pk>/', ClauseDetailView.as_view(), name='clause-detail'),
    # Step 10: Document-scoped AI chat preparation endpoints
    path('documents/<str:pk>/conversations/', DocumentConversationListCreateView.as_view(), name='document-conversations-list-create'),
    path('conversations/<str:pk>/', ConversationDetailView.as_view(), name='conversation-detail'),
    path('conversations/<str:pk>/messages/', ConversationMessageCreateView.as_view(), name='conversation-message-create'),
]

