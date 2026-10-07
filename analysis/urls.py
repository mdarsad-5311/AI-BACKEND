from django.urls import path
from analysis.views import (
    DocumentAnalysisView,
    DocumentReanalyzeView,
    DocumentRisksListView,
    RiskDetailView,
    ClauseAnalysisDetailView,
)

urlpatterns = [
    path('documents/<str:pk>/analysis/', DocumentAnalysisView.as_view(), name='document-analysis'),
    path('documents/<str:pk>/reanalyze/', DocumentReanalyzeView.as_view(), name='document-reanalyze'),
    path('documents/<str:pk>/risks/', DocumentRisksListView.as_view(), name='document-risks-list'),
    path('risks/<str:pk>/', RiskDetailView.as_view(), name='risk-detail'),
    path('clauses/<str:pk>/analysis/', ClauseAnalysisDetailView.as_view(), name='clause-analysis-detail'),
]
