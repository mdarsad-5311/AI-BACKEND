from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied

from documents.models import Document, Clause
from documents.views import get_document_for_user
from analysis.models import AIAnalysis, RiskFinding, ClauseAnalysis
from analysis.serializers import AIAnalysisSerializer, RiskFindingSerializer, ClauseAnalysisSerializer
from analysis.services import analyze_document


class DocumentAnalysisView(APIView):
    """
    GET /api/v1/documents/<id>/analysis/ - Comprehensive document analysis payload.
    Returns:
    {
      "document": { "id": "...", "title": "..." },
      "analysis": { "score": 78, "severity": "HIGH", "findings_breakdown": {...}, ... }
    }
    """
    def get(self, request, pk):
        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)

        # Check if analysis already exists
        if not hasattr(document, 'analysis'):
            # If document has extracted text, perform analysis automatically
            if (document.extracted_text or "").strip() or (document.extracted_pages or []):
                try:
                    analyze_document(document)
                except Exception:
                    return Response(
                        {'detail': 'Analysis has not been generated for this document yet.'},
                        status=status.HTTP_404_NOT_FOUND
                    )
            else:
                return Response(
                    {'detail': 'Analysis has not been generated for this document yet. Please extract text and analyze the document first.'},
                    status=status.HTTP_404_NOT_FOUND
                )

        analysis = document.analysis
        serializer = AIAnalysisSerializer(analysis)

        return Response({
            'document': {
                'id': document.id,
                'title': document.title,
                'file_name': document.file_name,
                'document_type': document.document_type,
            },
            'analysis': serializer.data
        }, status=status.HTTP_200_OK)


class DocumentReanalyzeView(APIView):
    """
    POST /api/v1/documents/<id>/reanalyze/ - Triggers deterministic analysis recalculation.
    """
    def post(self, request, pk):
        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)

        analysis = analyze_document(document)
        serializer = AIAnalysisSerializer(analysis)

        return Response({
            'detail': f'Document {document.id} re-analysis completed successfully.',
            'analysis': serializer.data
        }, status=status.HTTP_200_OK)


class DocumentRisksListView(APIView):
    """
    GET /api/v1/documents/<id>/risks/ - List all risks associated with a document.
    """
    def get(self, request, pk):
        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)

        risks = document.risks.all()
        serializer = RiskFindingSerializer(risks, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class RiskDetailView(APIView):
    """
    GET /api/v1/risks/<id>/ - Retrieve specific risk finding.
    """
    def get(self, request, pk):
        risk = get_object_or_404(RiskFinding, pk=pk)
        if request.user.is_authenticated and risk.document.user is not None and risk.document.user != request.user:
            return Response({'detail': 'You do not have permission to access this risk.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = RiskFindingSerializer(risk)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClauseAnalysisDetailView(APIView):
    """
    GET /api/v1/clauses/<id>/analysis/ - Detailed AI analysis and suggested redline for clause.
    """
    def get(self, request, pk):
        clause = get_object_or_404(Clause, pk=pk)
        if request.user.is_authenticated and clause.document.user is not None and clause.document.user != request.user:
            return Response({'detail': 'You do not have permission to access this clause analysis.'}, status=status.HTTP_403_FORBIDDEN)

        if not hasattr(clause, 'clause_analysis'):
            return Response(
                {'detail': 'Clause analysis is not yet generated for this clause.'},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ClauseAnalysisSerializer(clause.clause_analysis)
        return Response(serializer.data, status=status.HTTP_200_OK)

