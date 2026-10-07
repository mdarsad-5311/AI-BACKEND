from rest_framework import serializers
from analysis.models import AIAnalysis, RiskFinding, ClauseAnalysis
from documents.serializers import ClauseSerializer


class RiskFindingSerializer(serializers.ModelSerializer):
    # Frontend aliases
    clauseRef = serializers.CharField(source='clause_ref', read_only=True)
    affectedClauseId = serializers.SerializerMethodField()
    riskScore = serializers.IntegerField(source='risk_score', read_only=True)
    pageNumber = serializers.IntegerField(source='page_number', read_only=True)
    businessImpact = serializers.CharField(source='business_impact', read_only=True)

    class Meta:
        model = RiskFinding
        fields = [
            'id',
            'document',
            'clause',
            'title',
            'severity',
            'risk_score',
            'confidence',
            'page_number',
            'clause_ref',
            'description',
            'business_impact',
            'mitigation',
            'created_at',
            # Aliases
            'clauseRef',
            'affectedClauseId',
            'riskScore',
            'pageNumber',
            'businessImpact',
        ]

    def get_affectedClauseId(self, obj):
        return obj.clause.id if obj.clause else None


class ClauseAnalysisSerializer(serializers.ModelSerializer):
    # Frontend aliases
    clauseTitle = serializers.CharField(source='clause.title', read_only=True)
    pageNumber = serializers.IntegerField(source='clause.page_number', read_only=True)
    riskLevel = serializers.CharField(source='risk_level', read_only=True)
    riskScore = serializers.IntegerField(source='risk_score', read_only=True)
    recommendedAction = serializers.CharField(source='recommended_action', read_only=True)
    businessImpact = serializers.CharField(source='business_impact', read_only=True)
    suggestedRedline = serializers.CharField(source='suggested_redline', read_only=True)
    # Step 6 requested aliases
    risk_assessment = serializers.CharField(source='risk_level', read_only=True)
    risk_rationale = serializers.CharField(source='explanation', read_only=True)
    commercial_impact = serializers.CharField(source='business_impact', read_only=True)
    recommended_legal_action = serializers.CharField(source='recommended_action', read_only=True)

    class Meta:
        model = ClauseAnalysis
        fields = [
            'id',
            'clause',
            'risk_level',
            'risk_score',
            'confidence',
            'explanation',
            'business_impact',
            'recommended_action',
            'original_text',
            'suggested_redline',
            'created_at',
            # Aliases
            'clauseTitle',
            'pageNumber',
            'riskLevel',
            'riskScore',
            'recommendedAction',
            'businessImpact',
            'suggestedRedline',
            'risk_assessment',
            'risk_rationale',
            'commercial_impact',
            'recommended_legal_action',
        ]


class AIAnalysisSerializer(serializers.ModelSerializer):
    findings_breakdown = serializers.ReadOnlyField()
    risk_findings = RiskFindingSerializer(source='document.risks', many=True, read_only=True)
    clauses = ClauseSerializer(source='document.clauses', many=True, read_only=True)

    # Frontend camelCase aliases
    riskScore = serializers.IntegerField(source='score', read_only=True)
    riskLevel = serializers.CharField(source='severity', read_only=True)
    aiConfidence = serializers.IntegerField(source='confidence', read_only=True)
    summary = serializers.CharField(source='executive_summary', read_only=True)
    keyConcerns = serializers.ListField(source='key_concerns', read_only=True)
    businessImpactSummary = serializers.CharField(source='business_impact_summary', read_only=True)
    governingLaw = serializers.CharField(source='governing_law', read_only=True)
    effectiveDate = serializers.CharField(source='effective_date', read_only=True)
    analyzedAt = serializers.DateTimeField(source='analyzed_at', read_only=True)

    # Step 9 structured contract insights from analysis_data
    obligations = serializers.SerializerMethodField()
    importantTerms = serializers.SerializerMethodField()
    missingOrConcerning = serializers.SerializerMethodField()
    overallRisk = serializers.CharField(source='severity', read_only=True)
    contractType = serializers.CharField(source='contract_type', read_only=True)
    modelName = serializers.CharField(source='model_name', read_only=True)

    class Meta:
        model = AIAnalysis
        fields = [
            'id',
            'document',
            'contract_type',
            'score',
            'severity',
            'confidence',
            'executive_summary',
            'key_concerns',
            'business_impact_summary',
            'parties',
            'governing_law',
            'effective_date',
            'analysis_data',
            'model_name',
            'status',
            'analyzed_at',
            'findings_breakdown',
            'risk_findings',
            'clauses',
            # Aliases
            'riskScore',
            'riskLevel',
            'overallRisk',
            'contractType',
            'modelName',
            'aiConfidence',
            'summary',
            'keyConcerns',
            'businessImpactSummary',
            'governingLaw',
            'effectiveDate',
            'analyzedAt',
            'obligations',
            'importantTerms',
            'missingOrConcerning',
        ]

    def get_obligations(self, obj):
        data = obj.analysis_data or {}
        return data.get('obligations', [])

    def get_importantTerms(self, obj):
        data = obj.analysis_data or {}
        return data.get('important_terms', [])

    def get_missingOrConcerning(self, obj):
        data = obj.analysis_data or {}
        return data.get('missing_or_concerning', [])
