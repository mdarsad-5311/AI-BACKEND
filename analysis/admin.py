from django.contrib import admin
from analysis.models import AIAnalysis, RiskFinding, ClauseAnalysis


@admin.register(AIAnalysis)
class AIAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'document', 'score', 'severity', 'confidence', 'status', 'analyzed_at')
    list_filter = ('severity', 'status')
    search_fields = ('document__id', 'document__title', 'executive_summary')


@admin.register(RiskFinding)
class RiskFindingAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'document', 'severity', 'risk_score', 'confidence', 'page_number')
    list_filter = ('severity', 'page_number')
    search_fields = ('title', 'description', 'document__id')


@admin.register(ClauseAnalysis)
class ClauseAnalysisAdmin(admin.ModelAdmin):
    list_display = ('id', 'clause', 'risk_level', 'risk_score', 'confidence')
    list_filter = ('risk_level',)
    search_fields = ('clause__title', 'explanation', 'suggested_redline')
