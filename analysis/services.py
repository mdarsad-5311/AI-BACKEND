import time
from django.utils import timezone
from analysis.models import AIAnalysis, RiskFinding, ClauseAnalysis
from documents.models import Clause
from documents.services.ai_analyzer import analyze_document_text, AIAnalysisError


def analyze_document(document):
    """
    Performs AI legal document analysis for a Document.
    Consumes extracted text from Step 8, invokes ai_analyzer,
    and populates AIAnalysis, Clause, RiskFinding, and ClauseAnalysis records.
    """
    # 1. Update/create AIAnalysis record with status='processing'
    analysis, _ = AIAnalysis.objects.get_or_create(
        document=document,
        defaults={
            'id': f"ana-{document.id}",
            'score': 50,
            'severity': 'MEDIUM',
            'confidence': 94,
            'executive_summary': f"Analysis pending for {document.title}.",
            'contract_type': document.document_type,
            'status': 'processing'
        }
    )

    analysis.status = 'processing'
    analysis.save(update_fields=['status'])

    # 2. Invoke structured AI analyzer
    try:
        data = analyze_document_text(document)
    except AIAnalysisError:
        analysis.status = 'failed'
        analysis.save(update_fields=['status'])
        raise
    except Exception as e:
        analysis.status = 'failed'
        analysis.save(update_fields=['status'])
        raise AIAnalysisError(f"Unexpected analysis failure: {str(e)}")

    # 3. Synchronize AIAnalysis fields
    analysis.contract_type = data.get('contract_type', document.document_type)
    analysis.score = data.get('risk_score', 50)
    analysis.severity = data.get('overall_risk', 'MEDIUM').upper()
    analysis.confidence = 94
    analysis.executive_summary = data.get('summary', '')
    analysis.key_concerns = data.get('key_concerns', [])
    analysis.business_impact_summary = data.get('business_impact_summary', '')
    analysis.parties = data.get('parties', [])
    analysis.governing_law = data.get('governing_law', '')
    analysis.effective_date = data.get('effective_date', '')
    analysis.analysis_data = data
    analysis.model_name = data.get('model_name', 'docusense-ai-legal-v1')
    analysis.status = 'completed'
    analysis.analyzed_at = timezone.now()
    analysis.save()

    # 4. Synchronize Clauses and ClauseAnalysis
    for idx, c_data in enumerate(data.get('key_clauses', []), start=1):
        clause_id = f"cl-{document.id}-{idx}"
        clause, _ = Clause.objects.update_or_create(
            id=clause_id,
            defaults={
                'document': document,
                'section_number': c_data.get('section_number', f"Section {idx}"),
                'title': c_data.get('title', f"Clause {idx}"),
                'page_number': c_data.get('page_start', 1),
                'category': c_data.get('category', 'Liability'),
                'snippet': c_data.get('snippet', ''),
                'content': c_data.get('snippet', '')
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id=f"ca-{clause_id}",
            defaults={
                'clause': clause,
                'risk_level': c_data.get('risk_level', 'MEDIUM').upper(),
                'risk_score': c_data.get('risk_score', 50),
                'confidence': 95,
                'explanation': c_data.get('explanation', ''),
                'business_impact': c_data.get('business_impact', ''),
                'recommended_action': c_data.get('recommended_action', ''),
                'original_text': c_data.get('snippet', ''),
                'suggested_redline': c_data.get('suggested_redline', '')
            }
        )

    # 5. Synchronize RiskFindings
    for idx, r_data in enumerate(data.get('risks', []), start=1):
        rf_id = f"rk-{document.id}-{idx}"
        RiskFinding.objects.update_or_create(
            id=rf_id,
            defaults={
                'document': document,
                'title': r_data.get('title', f"Risk {idx}"),
                'severity': r_data.get('severity', 'MEDIUM').upper(),
                'risk_score': r_data.get('risk_score', 60),
                'confidence': r_data.get('confidence', 92),
                'page_number': r_data.get('page_start', 1),
                'clause_ref': r_data.get('clause_ref', ''),
                'description': r_data.get('description', ''),
                'business_impact': r_data.get('business_impact', ''),
                'mitigation': r_data.get('mitigation', '')
            }
        )

    # Mark document status as analyzed
    document.status = 'analyzed'
    document.save(update_fields=['status'])

    return analysis
