from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.response import Response
from rest_framework.views import APIView


class ApiDocsIndexView(APIView):
    """
    API Documentation & Directory route.
    """
    def get(self, request):
        return Response({
            'name': 'DocuSense AI REST API',
            'version': 'v1',
            'status': 'online',
            'description': 'Enterprise Document Intelligence & Contract Analysis API',
            'endpoints': {
                'documents': {
                    'list_create': '/api/v1/documents/',
                    'detail': '/api/v1/documents/<id>/',
                    'extract_text': '/api/v1/documents/<id>/extract/',
                    'analyze': '/api/v1/documents/<id>/analyze/',
                    'clauses': '/api/v1/documents/<id>/clauses/',
                    'clause_detail': '/api/v1/clauses/<id>/',
                    'conversations': '/api/v1/documents/<id>/conversations/',
                    'conversation_detail': '/api/v1/conversations/<id>/',
                    'conversation_messages': '/api/v1/conversations/<id>/messages/',
                },
                'analysis': {
                    'document_analysis': '/api/v1/documents/<id>/analysis/',
                    'reanalyze': '/api/v1/documents/<id>/reanalyze/',
                    'document_risks': '/api/v1/documents/<id>/risks/',
                    'risk_detail': '/api/v1/risks/<id>/',
                    'clause_analysis': '/api/v1/clauses/<id>/analysis/',
                }
            }
        })


urlpatterns = [
    path('', ApiDocsIndexView.as_view(), name='root-docs'),
    path('admin/', admin.site.urls),
    path('api/', ApiDocsIndexView.as_view(), name='api-index'),
    path('api/docs/', ApiDocsIndexView.as_view(), name='api-docs'),
    path('api/v1/', include('documents.urls')),
    path('api/v1/', include('analysis.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
