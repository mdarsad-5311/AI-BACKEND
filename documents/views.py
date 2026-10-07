import os
import uuid
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.shortcuts import get_object_or_404

from documents.models import Document, Clause
from documents.serializers import DocumentSerializer, ClauseSerializer
from analysis.services import analyze_document


from django.core.exceptions import PermissionDenied
from django.db.models import Q
from documents.models import Conversation, ChatMessage
from documents.serializers import ConversationSerializer, ChatMessageSerializer


def get_document_for_user(pk, user=None):
    """
    Retrieves document by ID and verifies user ownership when user is authenticated.
    Raises Http404 if not found, or PermissionDenied if document belongs to another user.
    """
    doc = get_object_or_404(Document, pk=pk)
    if user and user.is_authenticated and doc.user is not None and doc.user != user:
        raise PermissionDenied("You do not have permission to access this document.")
    return doc


class DocumentListCreateView(APIView):
    """
    GET  /api/v1/documents/ - List all accessible documents (scoped to authenticated user if logged in).
    POST /api/v1/documents/ - Upload new agreement file (multipart/form-data or JSON).
    """
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get(self, request):
        if request.user.is_authenticated:
            # Show documents belonging to user or global demo documents (user is None)
            documents = Document.objects.filter(Q(user=request.user) | Q(user__isnull=True))
        else:
            documents = Document.objects.all()

        serializer = DocumentSerializer(documents, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        uploaded_file = request.FILES.get('file')
        title = request.data.get('title')
        doc_type = request.data.get('document_type', 'Master Services Agreement')
        user = request.user if request.user.is_authenticated else None

        if uploaded_file:
            # File validation: extension
            original_name = uploaded_file.name or 'document'
            ext = os.path.splitext(original_name)[1].lower()
            allowed_extensions = ['.pdf', '.docx', '.doc', '.txt']
            if ext not in allowed_extensions:
                return Response(
                    {'error': 'Unsupported file type. Allowed formats: PDF, DOCX, DOC, TXT.', 'file': ['Unsupported file type. Allowed formats: PDF, DOCX, DOC, TXT.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # File validation: maximum size 50MB
            max_size = 50 * 1024 * 1024  # 50MB
            if uploaded_file.size > max_size:
                return Response(
                    {'error': 'File exceeds maximum allowed size of 50 MB.', 'file': ['File exceeds maximum allowed size of 50 MB.']},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Clean/safe title fallback
            if not title:
                base_name = os.path.splitext(os.path.basename(original_name))[0]
                title = base_name.replace('_', ' ').replace('-', ' ').strip().title() or 'Uploaded Document'

            # Human-readable file size format
            size_bytes = uploaded_file.size
            if size_bytes >= 1024 * 1024:
                file_size_str = f"{(size_bytes / (1024 * 1024)):.1f} MB"
            elif size_bytes >= 1024:
                file_size_str = f"{(size_bytes / 1024):.1f} KB"
            else:
                file_size_str = f"{size_bytes} B"

            # Auto-detect document type from title if default
            if doc_type == 'Master Services Agreement':
                lower_title = title.lower()
                if 'nda' in lower_title or 'confidential' in lower_title:
                    doc_type = 'Non-Disclosure Agreement'
                elif 'saas' in lower_title or 'cloud' in lower_title or 'license' in lower_title:
                    doc_type = 'SaaS Vendor Agreement'
                elif 'employment' in lower_title:
                    doc_type = 'Employment Agreement'
                elif 'sla' in lower_title or 'service level' in lower_title:
                    doc_type = 'Service Level Agreement'

            doc_id = f"doc-{uuid.uuid4().hex[:10]}"

            # Create document in 'uploaded' status for Step 7
            document = Document.objects.create(
                id=doc_id,
                user=user,
                title=title,
                file=uploaded_file,
                file_name=os.path.basename(original_name),
                file_size=file_size_str,
                page_count=1,
                document_type=doc_type,
                status='uploaded'
            )

            serializer = DocumentSerializer(document)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        # Handle case where file is missing in multipart upload
        if 'multipart/form-data' in request.content_type.lower() or not title:
            return Response(
                {'error': 'A file is required for document upload.', 'file': ['This field is required.']},
                status=status.HTTP_400_BAD_REQUEST
            )

        # JSON metadata creation
        doc_id = request.data.get('id', f"doc-{uuid.uuid4().hex[:10]}")
        document = Document.objects.create(
            id=doc_id,
            user=user,
            title=title,
            file_name=request.data.get('file_name', f"{title.replace(' ', '_')}.pdf"),
            file_size=request.data.get('file_size', '1.0 MB'),
            page_count=int(request.data.get('page_count', 1)),
            document_type=doc_type,
            status='uploaded'
        )

        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentDetailView(APIView):
    """
    GET    /api/v1/documents/<id>/ - Retrieve document metadata.
    DELETE /api/v1/documents/<id>/ - Remove document and associated findings.
    """
    def get(self, request, pk):
        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = DocumentSerializer(document)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)
        document.delete()
        return Response({'detail': f'Document {pk} deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


class DocumentClausesListView(APIView):
    """
    GET /api/v1/documents/<id>/clauses/ - List all clauses extracted for a specific document.
    """
    def get(self, request, pk):
        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)
        clauses = document.clauses.all()
        serializer = ClauseSerializer(clauses, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ClauseDetailView(APIView):
    """
    GET /api/v1/clauses/<id>/ - Retrieve specific clause details.
    """
    def get(self, request, pk):
        clause = get_object_or_404(Clause, pk=pk)
        if request.user.is_authenticated and clause.document.user is not None and clause.document.user != request.user:
            return Response({'detail': 'You do not have permission to access this clause.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ClauseSerializer(clause)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DocumentExtractTextView(APIView):
    """
    POST /api/v1/documents/<id>/extract/ - Extract text page-by-page from an uploaded PDF.
    """
    def post(self, request, pk):
        from django.utils import timezone
        from documents.services.pdf_extractor import extract_text_from_pdf, PDFExtractionError

        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)

        # Verify that uploaded file exists
        if not document.file:
            return Response(
                {
                    'id': document.id,
                    'status': 'failed',
                    'error': 'No file attached to this document.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check physical existence in storage
        if not document.file.storage.exists(document.file.name):
            return Response(
                {
                    'id': document.id,
                    'status': 'failed',
                    'error': 'Uploaded file not found in storage.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Verify file is a PDF
        ext = os.path.splitext(document.file.name)[1].lower()
        if ext != '.pdf':
            return Response(
                {
                    'id': document.id,
                    'status': 'failed',
                    'error': 'Only PDF documents support text extraction in this pipeline.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        # Mark document as processing
        document.status = 'processing'
        document.extraction_error = ''
        document.save(update_fields=['status', 'extraction_error'])

        try:
            # Safely open and extract text page-by-page
            with document.file.open('rb') as f:
                extraction_result = extract_text_from_pdf(f)

            document.extracted_text = extraction_result['text']
            document.extracted_pages = extraction_result['pages']
            document.page_count = extraction_result['page_count']
            document.status = 'analyzed'
            document.extracted_at = timezone.now()
            document.extraction_error = ''
            document.save(update_fields=[
                'extracted_text',
                'extracted_pages',
                'page_count',
                'status',
                'extracted_at',
                'extraction_error',
                'updated_at'
            ])

            return Response(
                {
                    'id': document.id,
                    'status': 'analyzed',
                    'page_count': document.page_count,
                    'message': 'PDF text extracted successfully.'
                },
                status=status.HTTP_200_OK
            )

        except PDFExtractionError as e:
            document.status = 'failed'
            document.extraction_error = str(e)
            document.save(update_fields=['status', 'extraction_error', 'updated_at'])
            return Response(
                {
                    'id': document.id,
                    'status': 'failed',
                    'error': 'Unable to extract text from PDF.'
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            document.status = 'failed'
            document.extraction_error = 'Unexpected extraction error'
            document.save(update_fields=['status', 'extraction_error', 'updated_at'])
            return Response(
                {
                    'id': document.id,
                    'status': 'failed',
                    'error': 'Unable to extract text from PDF.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class DocumentAnalyzeView(APIView):
    """
    POST /api/v1/documents/<id>/analyze/ - Perform AI contract analysis on extracted text.
    """
    def post(self, request, pk):
        from analysis.services import analyze_document
        from documents.services.ai_analyzer import AIAnalysisError

        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)

        # Validate that document has extracted text
        if not (document.extracted_text or "").strip() and not (document.extracted_pages or []):
            return Response(
                {
                    'id': document.id,
                    'status': 'failed',
                    'error': 'Document has no extracted text. Please run PDF text extraction first.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            analysis = analyze_document(document)
            return Response(
                {
                    'id': document.id,
                    'status': 'analyzed',
                    'analysis_id': analysis.id,
                    'overall_risk': analysis.severity.lower(),
                    'risk_score': analysis.score,
                    'message': 'Document analysis completed successfully.'
                },
                status=status.HTTP_200_OK
            )
        except AIAnalysisError as e:
            return Response(
                {
                    'id': document.id,
                    'status': 'failed',
                    'error': str(e)
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        except Exception as e:
            return Response(
                {
                    'id': document.id,
                    'status': 'failed',
                    'error': 'AI analysis failed unexpectedly.'
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# =========================================================================
# Step 10: Persistent AI Chat & Conversation Scaffolding
# =========================================================================

class DocumentConversationListCreateView(APIView):
    """
    GET  /api/v1/documents/<id>/conversations/ - List chat sessions on document.
    POST /api/v1/documents/<id>/conversations/ - Start new chat session on document.
    """
    def get(self, request, pk):
        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)

        conversations = document.conversations.all()
        if request.user.is_authenticated:
            conversations = conversations.filter(Q(user=request.user) | Q(user__isnull=True))

        serializer = ConversationSerializer(conversations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, pk):
        try:
            document = get_document_for_user(pk, request.user)
        except PermissionDenied:
            return Response({'detail': 'You do not have permission to access this document.'}, status=status.HTTP_403_FORBIDDEN)

        title = request.data.get('title', f"Inquiry on {document.title[:40]}")
        user = request.user if request.user.is_authenticated else None
        conv_id = f"conv-{uuid.uuid4().hex[:10]}"

        conversation = Conversation.objects.create(
            id=conv_id,
            user=user,
            document=document,
            title=title
        )
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ConversationDetailView(APIView):
    """
    GET    /api/v1/conversations/<id>/ - Retrieve conversation details and message history.
    DELETE /api/v1/conversations/<id>/ - Delete conversation session.
    """
    def get(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        if request.user.is_authenticated and conversation.user is not None and conversation.user != request.user:
            return Response({'detail': 'You do not have permission to access this conversation.'}, status=status.HTTP_403_FORBIDDEN)
        serializer = ConversationSerializer(conversation)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        if request.user.is_authenticated and conversation.user is not None and conversation.user != request.user:
            return Response({'detail': 'You do not have permission to access this conversation.'}, status=status.HTTP_403_FORBIDDEN)
        conversation.delete()
        return Response({'detail': f'Conversation {pk} deleted successfully.'}, status=status.HTTP_204_NO_CONTENT)


class ConversationMessageCreateView(APIView):
    """
    POST /api/v1/conversations/<id>/messages/ - Post user message to conversation.
    """
    def post(self, request, pk):
        conversation = get_object_or_404(Conversation, pk=pk)
        if request.user.is_authenticated and conversation.user is not None and conversation.user != request.user:
            return Response({'detail': 'You do not have permission to access this conversation.'}, status=status.HTTP_403_FORBIDDEN)

        content = request.data.get('content', '').strip()
        if not content:
            return Response({'error': 'Message content cannot be blank.'}, status=status.HTTP_400_BAD_REQUEST)

        role = request.data.get('role', 'user')
        page_refs = request.data.get('page_references', [])

        msg_id = f"msg-{uuid.uuid4().hex[:10]}"
        message = ChatMessage.objects.create(
            id=msg_id,
            conversation=conversation,
            role=role,
            content=content,
            page_references=page_refs
        )
        # Update conversation timestamp
        conversation.save()

        serializer = ChatMessageSerializer(message)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

