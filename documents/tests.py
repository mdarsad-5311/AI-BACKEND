from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient
from rest_framework import status

from documents.models import Document, Clause
from analysis.models import AIAnalysis, RiskFinding, ClauseAnalysis


class DocuSenseAPITests(TestCase):
    def setUp(self):
        self.client = APIClient()

        # Seed sample test document
        self.doc = Document.objects.create(
            id="test-doc-1",
            title="Enterprise Cloud Agreement",
            file_name="Enterprise_Cloud_Agreement.pdf",
            file_size="2.1 MB",
            page_count=3,
            document_type="Master Services Agreement",
            status="analyzed"
        )

        self.clause = Clause.objects.create(
            id="test-cl-1",
            document=self.doc,
            section_number="12.1",
            title="Section 12.1 - Indemnification Cap",
            page_number=2,
            category="Liability",
            snippet="Indemnification shall not be subject to aggregate caps.",
            content="Indemnification shall not be subject to aggregate caps."
        )

        self.clause_analysis = ClauseAnalysis.objects.create(
            id="test-ca-1",
            clause=self.clause,
            risk_level="HIGH",
            risk_score=85,
            confidence=95,
            explanation="Uncapped indemnification liability.",
            business_impact="Severe financial exposure.",
            recommended_action="Introduce mutual 2x contract value cap.",
            original_text=self.clause.snippet,
            suggested_redline="Aggregate indemnification shall not exceed two times fees."
        )

        self.risk = RiskFinding.objects.create(
            id="test-rk-1",
            document=self.doc,
            clause=self.clause,
            title="Uncapped Liability Exclusion",
            severity="HIGH",
            risk_score=85,
            confidence=95,
            page_number=2,
            clause_ref="Section 12.1",
            description="No monetary cap on indemnification breaches.",
            business_impact="Severe litigation downside.",
            mitigation="Cap liability at 2x fees."
        )

        self.analysis = AIAnalysis.objects.create(
            id="test-ana-1",
            document=self.doc,
            score=85,
            severity="HIGH",
            confidence=94,
            executive_summary="Agreement presents material uncapped indemnity risk.",
            key_concerns=["Uncapped liability in Section 12.1"],
            business_impact_summary="Litigation exposure without liability thresholds.",
            parties=["Enterprise Corp", "Vendor LLC"],
            governing_law="Delaware",
            status="completed"
        )

    # 1. Documents Endpoint Tests
    def test_list_documents(self):
        response = self.client.get('/api/v1/documents/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], "test-doc-1")
        self.assertEqual(response.data[0]['riskScore'], 85)

    def test_retrieve_document_success(self):
        response = self.client.get(f'/api/v1/documents/{self.doc.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Enterprise Cloud Agreement")

    def test_retrieve_document_not_found(self):
        response = self.client.get('/api/v1/documents/non-existent-id/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_document_json(self):
        data = {
            "title": "New SaaS Procurement Terms",
            "document_type": "SaaS Vendor Agreement"
        }
        response = self.client.post('/api/v1/documents/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Document.objects.filter(title="New SaaS Procurement Terms").exists())

    def test_create_document_file_upload(self):
        pdf_content = b"%PDF-1.4 mock binary stream test content"
        uploaded_file = SimpleUploadedFile("Uploaded_SOW.pdf", pdf_content, content_type="application/pdf")
        response = self.client.post(
            '/api/v1/documents/',
            {'file': uploaded_file, 'title': 'Uploaded SOW Statement'},
            format='multipart'
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'uploaded')
        created_doc = Document.objects.get(id=response.data['id'])
        self.assertTrue(created_doc.file)
        self.assertTrue(created_doc.file.storage.exists(created_doc.file.name))
        self.assertEqual(created_doc.file_name, "Uploaded_SOW.pdf")

        # Cleanup test file
        file_path = created_doc.file.name
        created_doc.delete()
        self.assertFalse(created_doc.file.storage.exists(file_path))

    def test_upload_supported_formats(self):
        for name, content_type in [
            ("contract.docx", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"),
            ("legacy_agreement.doc", "application/msword"),
            ("notes.txt", "text/plain")
        ]:
            f = SimpleUploadedFile(name, b"dummy text stream content", content_type=content_type)
            response = self.client.post('/api/v1/documents/', {'file': f}, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_201_CREATED)
            doc = Document.objects.get(id=response.data['id'])
            doc.delete()

    def test_upload_unsupported_format_rejected(self):
        for invalid_name in ["malware.exe", "photo.jpg", "image.png"]:
            bad_file = SimpleUploadedFile(invalid_name, b"binary content", content_type="application/octet-stream")
            response = self.client.post('/api/v1/documents/', {'file': bad_file}, format='multipart')
            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
            self.assertIn("error", response.data)
            self.assertIn("Unsupported file type", response.data['error'])

    def test_upload_missing_file_rejected(self):
        response = self.client.post('/api/v1/documents/', {}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("file", response.data)

    def test_upload_oversized_file_rejected(self):
        # Create an in-memory byte buffer exceeding 50MB (51MB)
        oversized_content = b"0" * (51 * 1024 * 1024)
        oversized_file = SimpleUploadedFile("massive_contract.pdf", oversized_content, content_type="application/pdf")
        response = self.client.post('/api/v1/documents/', {'file': oversized_file}, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("File exceeds maximum allowed size of 50 MB.", str(response.data))

    def test_upload_duplicate_filenames_remain_independent(self):
        file1 = SimpleUploadedFile("same_filename.pdf", b"first file version", content_type="application/pdf")
        file2 = SimpleUploadedFile("same_filename.pdf", b"second file version", content_type="application/pdf")

        r1 = self.client.post('/api/v1/documents/', {'file': file1}, format='multipart')
        r2 = self.client.post('/api/v1/documents/', {'file': file2}, format='multipart')

        self.assertEqual(r1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(r2.status_code, status.HTTP_201_CREATED)

        doc1 = Document.objects.get(id=r1.data['id'])
        doc2 = Document.objects.get(id=r2.data['id'])

        # Filename records should have distinct stored storage paths
        self.assertNotEqual(doc1.file.name, doc2.file.name)
        self.assertTrue(doc1.file.storage.exists(doc1.file.name))
        self.assertTrue(doc2.file.storage.exists(doc2.file.name))

        path1 = doc1.file.name
        path2 = doc2.file.name
        storage1 = doc1.file.storage

        # Cleanup
        doc1.delete()
        doc2.delete()
        self.assertFalse(storage1.exists(path1))
        self.assertFalse(storage1.exists(path2))

    def test_delete_document_cleans_up_storage(self):
        f = SimpleUploadedFile("cleanup_test.pdf", b"content to delete", content_type="application/pdf")
        r = self.client.post('/api/v1/documents/', {'file': f}, format='multipart')
        self.assertEqual(r.status_code, status.HTTP_201_CREATED)
        doc = Document.objects.get(id=r.data['id'])
        file_path = doc.file.name
        self.assertTrue(doc.file.storage.exists(file_path))

        # Delete document via API
        del_response = self.client.delete(f'/api/v1/documents/{doc.id}/')
        self.assertEqual(del_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Document.objects.filter(id=doc.id).exists())
        self.assertFalse(doc.file.storage.exists(file_path))

    # 2. Document Analysis Tests
    def test_retrieve_document_analysis(self):
        response = self.client.get(f'/api/v1/documents/{self.doc.id}/analysis/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('document', response.data)
        self.assertIn('analysis', response.data)
        self.assertEqual(response.data['analysis']['score'], 85)
        self.assertEqual(response.data['analysis']['findings_breakdown']['high'], 1)
        self.assertGreaterEqual(len(response.data['analysis']['risk_findings']), 1)

    def test_reanalyze_document(self):
        response = self.client.post(f'/api/v1/documents/{self.doc.id}/reanalyze/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['analysis']['status'], 'completed')

    # 3. Clauses and Risks Tests
    def test_list_document_clauses(self):
        response = self.client.get(f'/api/v1/documents/{self.doc.id}/clauses/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], "test-cl-1")
        self.assertEqual(response.data[0]['riskLevel'], "HIGH")

    def test_retrieve_clause_detail(self):
        response = self.client.get(f'/api/v1/clauses/{self.clause.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['title'], "Section 12.1 - Indemnification Cap")

    def test_retrieve_clause_analysis(self):
        response = self.client.get(f'/api/v1/clauses/{self.clause.id}/analysis/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['risk_level'], "HIGH")
        self.assertIn("suggested_redline", response.data)

    def test_list_document_risks(self):
        response = self.client.get(f'/api/v1/documents/{self.doc.id}/risks/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['title'], "Uncapped Liability Exclusion")

    def test_retrieve_risk_detail(self):
        response = self.client.get(f'/api/v1/risks/{self.risk.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['severity'], "HIGH")

    # 4. API Documentation Route Test
    def test_api_docs_route(self):
        response = self.client.get('/api/docs/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('endpoints', response.data)

    # 5. Step 8 PDF Text Extraction Tests
    def test_extract_pdf_single_page_success(self):
        pdf_raw = (
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
            b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
            b"5 0 obj\n<< /Length 55 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n"
            b"(Enterprise Legal Contract Terms) Tj\nET\nendstream\nendobj\nxref\n"
            b"0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
            b"0000000115 00000 n \n0000000229 00000 n \n0000000305 00000 n \n"
            b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n410\n%%EOF"
        )
        f = SimpleUploadedFile("single_page_agreement.pdf", pdf_raw, content_type="application/pdf")
        up_res = self.client.post('/api/v1/documents/', {'file': f}, format='multipart')
        self.assertEqual(up_res.status_code, status.HTTP_201_CREATED)
        doc_id = up_res.data['id']

        extract_res = self.client.post(f'/api/v1/documents/{doc_id}/extract/')
        self.assertEqual(extract_res.status_code, status.HTTP_200_OK)
        self.assertEqual(extract_res.data['status'], 'analyzed')
        self.assertEqual(extract_res.data['page_count'], 1)

        # Verify persisted fields in database
        updated_doc = Document.objects.get(id=doc_id)
        self.assertEqual(updated_doc.status, 'analyzed')
        self.assertIn("Enterprise Legal Contract Terms", updated_doc.extracted_text)
        self.assertEqual(len(updated_doc.extracted_pages), 1)
        self.assertEqual(updated_doc.extracted_pages[0]['page_number'], 1)
        self.assertIn("Enterprise Legal Contract Terms", updated_doc.extracted_pages[0]['text'])
        self.assertIsNotNone(updated_doc.extracted_at)
        updated_doc.delete()

    def test_extract_pdf_multi_page_success(self):
        import io
        from pypdf import PdfWriter, PdfReader
        pdf_raw = (
            b"%PDF-1.4\n1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
            b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
            b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
            b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
            b"5 0 obj\n<< /Length 55 >>\nstream\nBT\n/F1 12 Tf\n72 712 Td\n"
            b"(Enterprise Legal Contract Terms) Tj\nET\nendstream\nendobj\nxref\n"
            b"0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n"
            b"0000000115 00000 n \n0000000229 00000 n \n0000000305 00000 n \n"
            b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n410\n%%EOF"
        )
        reader = PdfReader(io.BytesIO(pdf_raw))
        writer = PdfWriter()
        writer.add_page(reader.pages[0])
        writer.add_page(reader.pages[0])
        writer.add_page(reader.pages[0])
        buf = io.BytesIO()
        writer.write(buf)

        f = SimpleUploadedFile("three_page_contract.pdf", buf.getvalue(), content_type="application/pdf")
        up_res = self.client.post('/api/v1/documents/', {'file': f}, format='multipart')
        doc_id = up_res.data['id']

        extract_res = self.client.post(f'/api/v1/documents/{doc_id}/extract/')
        self.assertEqual(extract_res.status_code, status.HTTP_200_OK)
        self.assertEqual(extract_res.data['page_count'], 3)

        updated_doc = Document.objects.get(id=doc_id)
        self.assertEqual(updated_doc.page_count, 3)
        self.assertEqual(len(updated_doc.extracted_pages), 3)
        self.assertEqual(updated_doc.extracted_pages[0]['page_number'], 1)
        self.assertEqual(updated_doc.extracted_pages[1]['page_number'], 2)
        self.assertEqual(updated_doc.extracted_pages[2]['page_number'], 3)
        updated_doc.delete()

    def test_extract_pdf_blank_page_handled_safely(self):
        import io
        from pypdf import PdfWriter
        writer = PdfWriter()
        writer.add_blank_page(width=300, height=300)
        buf = io.BytesIO()
        writer.write(buf)

        f = SimpleUploadedFile("blank_contract.pdf", buf.getvalue(), content_type="application/pdf")
        up_res = self.client.post('/api/v1/documents/', {'file': f}, format='multipart')
        doc_id = up_res.data['id']

        extract_res = self.client.post(f'/api/v1/documents/{doc_id}/extract/')
        self.assertEqual(extract_res.status_code, status.HTTP_200_OK)
        self.assertEqual(extract_res.data['page_count'], 1)
        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.extracted_text, "")
        self.assertEqual(doc.extracted_pages[0]['text'], "")
        doc.delete()

    def test_extract_pdf_corrupted_file_marks_failed(self):
        corrupted_content = b"%PDF-1.4 [corrupted header and broken body EOF"
        f = SimpleUploadedFile("corrupted.pdf", corrupted_content, content_type="application/pdf")
        up_res = self.client.post('/api/v1/documents/', {'file': f}, format='multipart')
        doc_id = up_res.data['id']

        extract_res = self.client.post(f'/api/v1/documents/{doc_id}/extract/')
        self.assertEqual(extract_res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
        self.assertEqual(extract_res.data['status'], 'failed')

        doc = Document.objects.get(id=doc_id)
        self.assertEqual(doc.status, 'failed')
        self.assertTrue(len(doc.extraction_error) > 0)
        # Original file remains intact in storage
        self.assertTrue(doc.file.storage.exists(doc.file.name))
        doc.delete()

    def test_extract_non_pdf_document_rejected(self):
        f = SimpleUploadedFile("agreement.docx", b"dummy docx bytes", content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        up_res = self.client.post('/api/v1/documents/', {'file': f}, format='multipart')
        doc_id = up_res.data['id']

        extract_res = self.client.post(f'/api/v1/documents/{doc_id}/extract/')
        self.assertEqual(extract_res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("Only PDF documents", extract_res.data['error'])
        doc = Document.objects.get(id=doc_id)
        doc.delete()

    def test_extract_missing_file_or_document_rejected(self):
        # Non-existent document
        res_404 = self.client.post('/api/v1/documents/non-existent-doc/extract/')
        self.assertEqual(res_404.status_code, status.HTTP_404_NOT_FOUND)

        # Document without file attached
        doc_no_file = Document.objects.create(
            id="doc-no-file-99",
            title="Empty Document",
            file=None,
            status="uploaded"
        )
        res_no_file = self.client.post(f'/api/v1/documents/{doc_no_file.id}/extract/')
        self.assertEqual(res_no_file.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res_no_file.data['status'], 'failed')
        doc_no_file.delete()

    # 6. Step 9 AI-Powered Contract Analysis Tests
    def test_analyze_requires_extracted_text(self):
        doc_empty = Document.objects.create(
            id="doc-no-text-test",
            title="Empty Extracted Doc",
            file_name="empty.pdf",
            extracted_text="",
            extracted_pages=[],
            status="uploaded"
        )
        res = self.client.post(f'/api/v1/documents/{doc_empty.id}/analyze/')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(res.data['status'], 'failed')
        self.assertIn("no extracted text", res.data['error'])
        doc_empty.delete()

    def test_analyze_document_success_deterministic(self):
        doc_with_text = Document.objects.create(
            id="doc-analyze-success",
            title="Acme Master Software License Agreement",
            file_name="Acme_SLA.pdf",
            extracted_text="Section 12.1 Indemnification. Contractor indemnifies Customer for third party IP claims without limitation. Section 14 Termination on 14 days notice.",
            extracted_pages=[
                {"page_number": 1, "text": "Section 12.1 Indemnification. Contractor indemnifies Customer for third party IP claims without limitation."},
                {"page_number": 2, "text": "Section 14 Termination on 14 days notice."}
            ],
            status="analyzed"
        )

        res = self.client.post(f'/api/v1/documents/{doc_with_text.id}/analyze/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['status'], 'analyzed')
        self.assertIn("overall_risk", res.data)
        self.assertIn("risk_score", res.data)

        # Confirm persisted AIAnalysis record
        doc_with_text.refresh_from_db()
        self.assertTrue(hasattr(doc_with_text, 'analysis'))
        ana = doc_with_text.analysis
        self.assertEqual(ana.status, 'completed')
        self.assertGreaterEqual(ana.score, 0)
        self.assertTrue(len(ana.executive_summary) > 0)
        self.assertIn("obligations", ana.analysis_data)
        self.assertIn("important_terms", ana.analysis_data)

        # Confirm GET /api/v1/documents/<id>/analysis/ returns full structured payload
        get_res = self.client.get(f'/api/v1/documents/{doc_with_text.id}/analysis/')
        self.assertEqual(get_res.status_code, status.HTTP_200_OK)
        self.assertIn('document', get_res.data)
        self.assertIn('analysis', get_res.data)
        self.assertIn('obligations', get_res.data['analysis'])
        self.assertIn('importantTerms', get_res.data['analysis'])
        self.assertIn('missingOrConcerning', get_res.data['analysis'])

        doc_with_text.delete()

    def test_analyze_document_reanalysis_idempotency(self):
        doc_re = Document.objects.create(
            id="doc-reanalyze-test",
            title="Vendor Consulting MSA",
            file_name="Vendor_MSA.pdf",
            extracted_text="Section 5 Limitation of Liability. Liability capped at fees paid in past 12 months.",
            extracted_pages=[{"page_number": 1, "text": "Section 5 Limitation of Liability. Liability capped at fees paid in past 12 months."}],
            status="analyzed"
        )

        # First call
        r1 = self.client.post(f'/api/v1/documents/{doc_re.id}/analyze/')
        self.assertEqual(r1.status_code, status.HTTP_200_OK)
        initial_ana_id = r1.data['analysis_id']

        # Second call should update existing analysis, not create duplicates
        r2 = self.client.post(f'/api/v1/documents/{doc_re.id}/analyze/')
        self.assertEqual(r2.status_code, status.HTTP_200_OK)
        self.assertEqual(r2.data['analysis_id'], initial_ana_id)

        # Assert exactly one AIAnalysis record exists for this document
        self.assertEqual(AIAnalysis.objects.filter(document=doc_re).count(), 1)
        doc_re.delete()

    def test_analyze_with_mocked_ai_provider(self):
        from unittest.mock import patch

        mock_ai_output = {
            "summary": "Mocked OpenAI assessment of SaaS license agreement.",
            "contract_type": "SaaS Vendor Agreement",
            "overall_risk": "high",
            "risk_score": 77,
            "parties": ["Alpha Corp", "Beta LLC"],
            "effective_date": "January 15, 2026",
            "governing_law": "State of New York, USA",
            "key_concerns": ["Uncapped security breach damages"],
            "business_impact_summary": "High financial downside risk",
            "key_clauses": [
                {
                    "title": "Data Security & Breach Notice",
                    "section_number": "Section 8.3",
                    "category": "Compliance",
                    "summary": "Requires 24 hour notice of security incidents.",
                    "snippet": "Vendor shall report unauthorized breaches within 24 hours.",
                    "risk_level": "medium",
                    "risk_score": 60,
                    "page_start": 1,
                    "page_end": 1
                }
            ],
            "risks": [
                {
                    "title": "Aggressive Security Notification Timeline",
                    "category": "Compliance Risk",
                    "description": "24 hours is unusually narrow for complex root cause forensics.",
                    "severity": "medium",
                    "risk_score": 62,
                    "confidence": 95,
                    "page_start": 1,
                    "page_end": 1
                }
            ],
            "obligations": [
                {"party": "Beta LLC", "description": "Maintain ISO 27001 compliance certificate", "page_start": 1}
            ],
            "important_terms": [
                {"term": "Notice Window", "value": "24 Hours", "page_start": 1}
            ],
            "missing_or_concerning": [
                {"title": "Lack of Force Majeure", "description": "No excusable delay protection for network grid outages"}
            ]
        }

        doc = Document.objects.create(
            id="doc-mock-ai",
            title="Cloud Data Services SOW",
            file_name="Cloud_Data.pdf",
            extracted_text="Vendor shall report unauthorized breaches within 24 hours.",
            extracted_pages=[{"page_number": 1, "text": "Vendor shall report unauthorized breaches within 24 hours."}],
            status="analyzed"
        )

        with patch("documents.services.ai_analyzer.call_ai_provider", return_value=mock_ai_output):
            res = self.client.post(f'/api/v1/documents/{doc.id}/analyze/')
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            self.assertEqual(res.data['overall_risk'], 'high')
            self.assertEqual(res.data['risk_score'], 77)

            doc.refresh_from_db()
            self.assertEqual(doc.analysis.executive_summary, "Mocked OpenAI assessment of SaaS license agreement.")
            self.assertEqual(doc.analysis.governing_law, "State of New York, USA")
            self.assertEqual(len(doc.analysis.analysis_data['obligations']), 1)

        doc.delete()

    def test_analyze_handles_ai_failure_cleanly(self):
        from unittest.mock import patch
        from documents.services.ai_analyzer import AIAnalysisError

        doc = Document.objects.create(
            id="doc-fail-ai",
            title="Failing Contract Doc",
            file_name="Fail.pdf",
            extracted_text="Sample contract terms.",
            extracted_pages=[{"page_number": 1, "text": "Sample contract terms."}],
            status="analyzed"
        )

        with patch("documents.services.ai_analyzer.call_ai_provider", side_effect=AIAnalysisError("AI provider quota exceeded")):
            res = self.client.post(f'/api/v1/documents/{doc.id}/analyze/')
            self.assertEqual(res.status_code, status.HTTP_422_UNPROCESSABLE_ENTITY)
            self.assertEqual(res.data['status'], 'failed')
            self.assertIn("AI provider quota exceeded", res.data['error'])

        doc.delete()


class DocuSenseStep10DatabaseTests(TestCase):
    """
    Step 10 Database Integration Tests:
    - User ownership and isolation on documents
    - Analysis persistence and relationship integrity
    - Idempotent re-analysis without duplicate records
    - Conversation and ChatMessage models
    - Cross-user unauthorized access prevention
    """
    def setUp(self):
        from django.contrib.auth import get_user_model
        from documents.models import Conversation, ChatMessage

        User = get_user_model()
        self.user_a = User.objects.create_user(username="lawyer_alice", password="password_alice")
        self.user_b = User.objects.create_user(username="lawyer_bob", password="password_bob")

        self.client_a = APIClient()
        self.client_a.force_authenticate(user=self.user_a)

        self.client_b = APIClient()
        self.client_b.force_authenticate(user=self.user_b)

        self.doc_a = Document.objects.create(
            id="doc-alice-10",
            user=self.user_a,
            title="Alice Private Master Agreement",
            file_name="Alice_Contract.pdf",
            document_type="Master Services Agreement",
            status="analyzed",
            extracted_text="Section 1. Payment Terms: Net 30 days. Section 2. Governing Law: State of Delaware.",
            extracted_pages=[
                {"page_number": 1, "text": "Section 1. Payment Terms: Net 30 days. Section 2. Governing Law: State of Delaware."}
            ]
        )

    def test_document_ownership_enforcement(self):
        # Alice can retrieve her document
        res_a = self.client_a.get(f'/api/v1/documents/{self.doc_a.id}/')
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        self.assertEqual(res_a.data['id'], self.doc_a.id)
        self.assertEqual(res_a.data['userId'], str(self.user_a.id))

        # Bob cannot retrieve Alice's document (returns 403 Forbidden)
        res_b = self.client_b.get(f'/api/v1/documents/{self.doc_a.id}/')
        self.assertEqual(res_b.status_code, status.HTTP_403_FORBIDDEN)

    def test_analysis_persistence_and_ownership_inheritance(self):
        # Analyze Alice's document via Alice's client
        res = self.client_a.post(f'/api/v1/documents/{self.doc_a.id}/analyze/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        self.doc_a.refresh_from_db()
        self.assertTrue(hasattr(self.doc_a, 'analysis'))
        self.assertIsNotNone(self.doc_a.analysis)
        self.assertEqual(self.doc_a.analysis.status, 'completed')

        # Verify Bob cannot view Alice's analysis
        res_b = self.client_b.get(f'/api/v1/documents/{self.doc_a.id}/analysis/')
        self.assertEqual(res_b.status_code, status.HTTP_403_FORBIDDEN)

        # Alice can view her analysis
        res_a = self.client_a.get(f'/api/v1/documents/{self.doc_a.id}/analysis/')
        self.assertEqual(res_a.status_code, status.HTTP_200_OK)
        self.assertIn("analysis", res_a.data)

    def test_reanalysis_prevents_duplicate_records(self):
        # Initial analysis
        self.client_a.post(f'/api/v1/documents/{self.doc_a.id}/analyze/')
        initial_analysis_count = AIAnalysis.objects.filter(document=self.doc_a).count()
        self.assertEqual(initial_analysis_count, 1)

        # Reanalyze via endpoint
        res = self.client_a.post(f'/api/v1/documents/{self.doc_a.id}/reanalyze/')
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        # Still exactly 1 AIAnalysis record
        self.assertEqual(AIAnalysis.objects.filter(document=self.doc_a).count(), 1)

    def test_conversation_and_chat_message_persistence(self):
        from documents.models import Conversation, ChatMessage

        # Alice creates conversation on her document
        res_create = self.client_a.post(
            f'/api/v1/documents/{self.doc_a.id}/conversations/',
            {'title': 'Payment Terms Review'},
            format='json'
        )
        self.assertEqual(res_create.status_code, status.HTTP_201_CREATED)
        conv_id = res_create.data['id']
        self.assertEqual(res_create.data['title'], 'Payment Terms Review')
        self.assertEqual(res_create.data['documentId'], self.doc_a.id)

        # Alice posts a message
        res_msg = self.client_a.post(
            f'/api/v1/conversations/{conv_id}/messages/',
            {
                'role': 'user',
                'content': 'What is the payment schedule?',
                'page_references': [1]
            },
            format='json'
        )
        self.assertEqual(res_msg.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res_msg.data['role'], 'user')
        self.assertEqual(res_msg.data['page_references'], [1])

        # Bob cannot access Alice's conversation
        res_b = self.client_b.get(f'/api/v1/conversations/{conv_id}/')
        self.assertEqual(res_b.status_code, status.HTTP_403_FORBIDDEN)

        # Alice retrieves conversation history
        res_detail = self.client_a.get(f'/api/v1/conversations/{conv_id}/')
        self.assertEqual(res_detail.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res_detail.data['messages']), 1)
        self.assertEqual(res_detail.data['messages'][0]['content'], 'What is the payment schedule?')

    def test_cascade_delete_cleans_up_relations(self):
        from documents.models import Conversation, ChatMessage

        conv = Conversation.objects.create(
            id="conv-cascade-test",
            user=self.user_a,
            document=self.doc_a,
            title="Cascade Test"
        )
        ChatMessage.objects.create(
            id="msg-cascade-test",
            conversation=conv,
            role="user",
            content="Test cascade deletion."
        )

        self.assertEqual(Conversation.objects.filter(id="conv-cascade-test").count(), 1)
        self.assertEqual(ChatMessage.objects.filter(id="msg-cascade-test").count(), 1)

        # Deleting the document cascades to conversations and messages
        self.doc_a.delete()

        self.assertEqual(Document.objects.filter(id="doc-alice-10").count(), 0)
        self.assertEqual(Conversation.objects.filter(id="conv-cascade-test").count(), 0)
        self.assertEqual(ChatMessage.objects.filter(id="msg-cascade-test").count(), 0)

