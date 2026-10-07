from rest_framework import serializers
from documents.models import Document, Clause


class ClauseSerializer(serializers.ModelSerializer):
    # Map to frontend compatibility fields
    riskLevel = serializers.SerializerMethodField()
    riskScore = serializers.SerializerMethodField()
    confidence = serializers.SerializerMethodField()
    explanation = serializers.SerializerMethodField()
    businessImpact = serializers.SerializerMethodField()
    recommendedAction = serializers.SerializerMethodField()
    suggestedRedline = serializers.SerializerMethodField()

    class Meta:
        model = Clause
        fields = [
            'id',
            'section_number',
            'title',
            'page_number',
            'category',
            'snippet',
            'content',
            'created_at',
            # CamelCase frontend fields
            'riskLevel',
            'riskScore',
            'confidence',
            'explanation',
            'businessImpact',
            'recommendedAction',
            'suggestedRedline',
        ]

    def get_riskLevel(self, obj):
        if hasattr(obj, 'clause_analysis'):
            return obj.clause_analysis.risk_level
        return 'LOW'

    def get_riskScore(self, obj):
        if hasattr(obj, 'clause_analysis'):
            return obj.clause_analysis.risk_score
        return 20

    def get_confidence(self, obj):
        if hasattr(obj, 'clause_analysis'):
            return obj.clause_analysis.confidence
        return 94

    def get_explanation(self, obj):
        if hasattr(obj, 'clause_analysis'):
            return obj.clause_analysis.explanation
        return ''

    def get_businessImpact(self, obj):
        if hasattr(obj, 'clause_analysis'):
            return obj.clause_analysis.business_impact
        return ''

    def get_recommendedAction(self, obj):
        if hasattr(obj, 'clause_analysis'):
            return obj.clause_analysis.recommended_action
        return ''

    def get_suggestedRedline(self, obj):
        if hasattr(obj, 'clause_analysis'):
            return obj.clause_analysis.suggested_redline
        return ''


class DocumentSerializer(serializers.ModelSerializer):
    # Frontend compatibility fields
    filename = serializers.CharField(source='file_name', read_only=True)
    fileSize = serializers.CharField(source='file_size', read_only=True)
    pageCount = serializers.IntegerField(source='page_count', read_only=True)
    documentType = serializers.CharField(source='document_type', read_only=True)
    uploadedAt = serializers.DateTimeField(source='created_at', read_only=True)
    riskScore = serializers.SerializerMethodField()
    riskLevel = serializers.SerializerMethodField()
    userId = serializers.CharField(source='user.id', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Document
        fields = [
            'id',
            'user',
            'userId',
            'username',
            'title',
            'file',
            'file_name',
            'file_size',
            'page_count',
            'document_type',
            'status',
            'extracted_text',
            'extracted_pages',
            'extraction_error',
            'extracted_at',
            'created_at',
            'updated_at',
            # Aliases for frontend direct consumption
            'filename',
            'fileSize',
            'pageCount',
            'documentType',
            'uploadedAt',
            'riskScore',
            'riskLevel',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'extracted_at', 'user', 'userId', 'username']

    def get_riskScore(self, obj):
        if hasattr(obj, 'analysis'):
            return obj.analysis.score
        return 0

    def get_riskLevel(self, obj):
        if hasattr(obj, 'analysis'):
            return obj.analysis.severity
        return 'LOW'


from documents.models import Conversation, ChatMessage


class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = [
            'id',
            'conversation',
            'role',
            'content',
            'page_references',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class ConversationSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)
    messageCount = serializers.SerializerMethodField()
    userId = serializers.CharField(source='user.id', read_only=True)
    documentId = serializers.CharField(source='document.id', read_only=True)

    class Meta:
        model = Conversation
        fields = [
            'id',
            'user',
            'userId',
            'document',
            'documentId',
            'title',
            'created_at',
            'updated_at',
            'messages',
            'messageCount',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'userId']

    def get_messageCount(self, obj):
        return obj.messages.count()

