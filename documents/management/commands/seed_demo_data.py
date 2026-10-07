from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from documents.models import Document, Clause, Conversation, ChatMessage
from analysis.models import AIAnalysis, RiskFinding, ClauseAnalysis

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds initial demo contracts and structured AI analyses (doc-1, doc-2, doc-3)"

    def handle(self, *args, **options):
        self.stdout.write("Seeding DocuSense AI demo documents and analyses...")

        # Ensure demo user exists
        demo_user, _ = User.objects.get_or_create(
            username="demo_lawyer",
            defaults={
                "email": "demo@docusense.ai",
                "first_name": "Demo",
                "last_name": "Counsel",
                "is_staff": False,
            }
        )
        if not demo_user.has_usable_password():
            demo_user.set_password("demo12345")
            demo_user.save()

        # =========================================================================
        # DOCUMENT 1: Global Enterprise Master Services Agreement
        # =========================================================================
        doc1_text_p1 = "GLOBAL ENTERPRISE MASTER SERVICES AGREEMENT\nEffective Date: November 1, 2026\nParties: Acme Global Logistics Inc. and OmniTech Solutions Corp.\nScope: Enterprise software architecture and systems engineering."
        doc1_text_p2 = "SECTION 9.4 PRE-EXISTING IP & DERIVATIVE WORKS: All custom developments, including modifications to Vendor Core Frameworks developed during this project, shall be deemed works made for hire.\nSECTION 12.2 INDEMNIFICATION CAP EXCLUSIONS: Neither party's liability under Section 11 or Section 12 shall be subject to any monetary cap or aggregate liability limitations."
        doc1_text_p3 = "SECTION 14.1 UNILATERAL TERMINATION FOR CONVENIENCE: Client may terminate this Agreement and any active Statement of Work immediately upon 14 days written notice without penalty.\nSECTION 16.4 GOVERNING LAW: Delaware law with exclusive dispute jurisdiction in the Delaware Court of Chancery."

        doc1, _ = Document.objects.update_or_create(
            id="doc-1",
            defaults={
                "user": demo_user,
                "title": "Global Enterprise Master Services Agreement",
                "file_name": "MSA_AcmeCorp_Enterprise_2026.pdf",
                "file_size": "2.4 MB",
                "page_count": 3,
                "document_type": "Master Services Agreement",
                "status": "analyzed",
                "extracted_text": f"{doc1_text_p1}\n\n{doc1_text_p2}\n\n{doc1_text_p3}",
                "extracted_pages": [
                    {"page_number": 1, "text": doc1_text_p1},
                    {"page_number": 2, "text": doc1_text_p2},
                    {"page_number": 3, "text": doc1_text_p3},
                ],
            }
        )

        cl1_1, _ = Clause.objects.update_or_create(
            id="cl-1",
            defaults={
                "document": doc1,
                "section_number": "12.2",
                "title": "Section 12.2 - Indemnification Cap Exclusions",
                "page_number": 2,
                "category": "Liability",
                "snippet": "Neither party's liability under Section 11 (Confidentiality) or Section 12 (Indemnification) shall be subject to any monetary cap or aggregate liability limitations.",
                "content": "Neither party's liability under Section 11 (Confidentiality) or Section 12 (Indemnification) shall be subject to any monetary cap or aggregate liability limitations.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-1",
            defaults={
                "clause": cl1_1,
                "risk_level": "HIGH",
                "risk_score": 88,
                "confidence": 96,
                "explanation": "Carves out confidentiality, data security, and indemnification breaches from standard 12-month aggregate fee cap, creating open-ended financial exposure in standard commercial operations.",
                "business_impact": "Exposes enterprise to unlimited commercial litigation damages and disproportionate third-party indemnification payouts without catastrophic threshold limitations.",
                "recommended_action": "Insert mutual super-cap explicitly restricted to two times (2x) the trailing 12-month contract fees paid under the applicable SOW.",
                "original_text": cl1_1.snippet,
                "suggested_redline": "Neither party's aggregate liability under Section 11 or Section 12 shall exceed two times (2x) the total fees paid or payable by Client under the applicable SOW in the twelve (12) months preceding the claim.",
            }
        )

        cl1_2, _ = Clause.objects.update_or_create(
            id="cl-2",
            defaults={
                "document": doc1,
                "section_number": "14.1",
                "title": "Section 14.1 - Unilateral Termination for Convenience",
                "page_number": 3,
                "category": "Termination",
                "snippet": "Client may terminate this Agreement and any active Statement of Work immediately upon 14 days written notice without penalty or early termination fees.",
                "content": "Client may terminate this Agreement and any active Statement of Work immediately upon 14 days written notice without penalty or early termination fees.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-2",
            defaults={
                "clause": cl1_2,
                "risk_level": "MEDIUM",
                "risk_score": 58,
                "confidence": 92,
                "explanation": "Client holds unilateral discretion to cancel ongoing project engagements without compensating for committed infrastructure, dedicated staffing, or sunk onboarding investments.",
                "business_impact": "Operational margin volatility and stranded resource overhead if high-capital deployments are abruptly cancelled midway through delivery.",
                "recommended_action": "Negotiate minimum 45-day prior written notice requirement plus mandatory reimbursement of unamortized development hardware and non-cancelable third-party licenses.",
                "original_text": cl1_2.snippet,
                "suggested_redline": "Client may terminate this Agreement upon forty-five (45) days prior written notice, subject to payment of all completed milestones and non-cancelable third-party commitments incurred through termination date.",
            }
        )

        cl1_3, _ = Clause.objects.update_or_create(
            id="cl-3",
            defaults={
                "document": doc1,
                "section_number": "9.4",
                "title": "Section 9.4 - Pre-existing IP & Derivative Works",
                "page_number": 2,
                "category": "Intellectual Property",
                "snippet": "All custom developments, including modifications to Vendor Core Frameworks developed during this project, shall be deemed works made for hire and owned exclusively by Client.",
                "content": "All custom developments, including modifications to Vendor Core Frameworks developed during this project, shall be deemed works made for hire and owned exclusively by Client.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-3",
            defaults={
                "clause": cl1_3,
                "risk_level": "CRITICAL",
                "risk_score": 95,
                "confidence": 98,
                "explanation": "Language establishes that any modular enhancements, adapters, or architectural extensions to vendor background frameworks become exclusive client property as works made for hire.",
                "business_impact": "Risk of forfeiting proprietary foundational software accelerators, creating IP contamination that could paralyze core platform reusability across other clients.",
                "recommended_action": "Strike 'modifications to Vendor Core Frameworks' from works made for hire and insert Schedule D retaining Vendor Background IP with non-exclusive client runtime license.",
                "original_text": cl1_3.snippet,
                "suggested_redline": "Custom deliverables created solely for Client shall be owned by Client. Provided, however, Vendor retains exclusive ownership of all Vendor Pre-Existing IP, core frameworks, and generalized enhancements thereof.",
            }
        )

        cl1_4, _ = Clause.objects.update_or_create(
            id="cl-4",
            defaults={
                "document": doc1,
                "section_number": "3.2",
                "title": "Section 3.2 - Service Deliverables & Acceptance Testing",
                "page_number": 1,
                "category": "Compliance",
                "snippet": "Customer shall have forty-five (45) business days following receipt of each Milestone Deliverable to conduct User Acceptance Testing against technical specifications.",
                "content": "Customer shall have forty-five (45) business days following receipt of each Milestone Deliverable to conduct User Acceptance Testing against technical specifications.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-4",
            defaults={
                "clause": cl1_4,
                "risk_level": "LOW",
                "risk_score": 24,
                "confidence": 89,
                "explanation": "Lengthy acceptance testing window that requires formal written sign-off before invoice generation.",
                "business_impact": "Potential minor delay in milestone billing cycles if testing feedback is prolonged.",
                "recommended_action": "Include deemed acceptance clause if customer fails to submit documented deficiency notice within 15 business days.",
                "original_text": cl1_4.snippet,
                "suggested_redline": "Deliverables shall be deemed accepted if Customer does not provide written notification of non-conformities within fifteen (15) business days of delivery.",
            }
        )

        cl1_5, _ = Clause.objects.update_or_create(
            id="cl-5",
            defaults={
                "document": doc1,
                "section_number": "16.4",
                "title": "Section 16.4 - Governing Law & Venue Jurisdiction",
                "page_number": 3,
                "category": "Compliance",
                "snippet": "This Agreement shall be governed by Delaware law with exclusive dispute jurisdiction in the Delaware Court of Chancery.",
                "content": "This Agreement shall be governed by Delaware law with exclusive dispute jurisdiction in the Delaware Court of Chancery.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-5",
            defaults={
                "clause": cl1_5,
                "risk_level": "LOW",
                "risk_score": 18,
                "confidence": 95,
                "explanation": "Standard well-defined commercial arbitration and corporate litigation forum.",
                "business_impact": "Neutral, predictable judicial interpretation with established precedent for technology transactions.",
                "recommended_action": "Maintain as standard enterprise jurisdiction.",
                "original_text": cl1_5.snippet,
                "suggested_redline": "Retain current Delaware choice of law and Chancery Court forum selection.",
            }
        )

        # Risks for doc-1
        RiskFinding.objects.update_or_create(
            id="rk-1",
            defaults={
                "document": doc1,
                "clause": cl1_3,
                "title": "IP Contamination of Core Frameworks",
                "severity": "CRITICAL",
                "risk_score": 95,
                "confidence": 98,
                "page_number": 2,
                "clause_ref": "Section 9.4",
                "description": "Clause 9.4 designates modifications to vendor foundational frameworks as works made for hire transferred exclusively to client.",
                "business_impact": "Risk of forfeiting foundational software accelerators and core architectural IP.",
                "mitigation": "Carve out vendor background technology and limit client assignment strictly to client-specific data models and custom reports.",
            }
        )

        RiskFinding.objects.update_or_create(
            id="rk-2",
            defaults={
                "document": doc1,
                "clause": cl1_1,
                "title": "Unlimited Liability for Data & Security Incidents",
                "severity": "HIGH",
                "risk_score": 88,
                "confidence": 96,
                "page_number": 2,
                "clause_ref": "Section 12.2",
                "description": "No aggregate ceiling or monetary cap on indemnity obligations or confidentiality breaches under Section 12.2.",
                "business_impact": "Uncapped exposure in the event of third-party indemnification or data incident claims.",
                "mitigation": "Negotiate a distinct liability super-cap tied to 2x annual contract value for confidentiality and security claims.",
            }
        )

        RiskFinding.objects.update_or_create(
            id="rk-3",
            defaults={
                "document": doc1,
                "clause": cl1_2,
                "title": "Asymmetrical 14-Day Cancellation Window",
                "severity": "MEDIUM",
                "risk_score": 58,
                "confidence": 92,
                "page_number": 3,
                "clause_ref": "Section 14.1",
                "description": "Client may terminate active SOWs with only 14 days notice and zero break fees, creating revenue cliff risks.",
                "business_impact": "Unamortized engineering overhead and sudden project descheduling without recourse.",
                "mitigation": "Extend notice to 45 days and require payment for all milestone work-in-progress plus committed expenses.",
            }
        )

        AIAnalysis.objects.update_or_create(
            id="ana-1",
            defaults={
                "document": doc1,
                "score": 78,
                "severity": "HIGH",
                "confidence": 94,
                "executive_summary": "This agreement contains several clauses that create material commercial and legal exposure, particularly around uncapped liability exclusions, unilateral termination rights without severance/unwinding fees, and broad works-made-for-hire assignment that threatens background IP.",
                "key_concerns": [
                    "Uncapped liability for confidentiality and indemnification under Section 12.2 carves out claims from the master fee limit.",
                    "Overly broad IP assignment in Section 9.4 transfers vendor core framework modifications to the client.",
                    "Asymmetrical 14-day cancellation without compensation for committed engineering capacity."
                ],
                "business_impact_summary": "Severe downside exposure in litigation or cybersecurity incidents; potential forfeiture of reusable software accelerators.",
                "parties": ["Acme Global Logistics Inc.", "OmniTech Solutions Corp."],
                "effective_date": "November 1, 2026",
                "governing_law": "State of Delaware, USA",
                "status": "completed",
            }
        )

        # =========================================================================
        # DOCUMENT 2: Cloud Infrastructure SaaS Vendor Agreement
        # =========================================================================
        doc2, _ = Document.objects.update_or_create(
            id="doc-2",
            defaults={
                "title": "Cloud Infrastructure SaaS Vendor Agreement",
                "file_name": "CloudStream_Vendor_Subscription_2026.pdf",
                "file_size": "1.1 MB",
                "page_count": 2,
                "document_type": "SaaS Vendor Agreement",
                "status": "analyzed",
            }
        )

        cl2_1, _ = Clause.objects.update_or_create(
            id="cl-201",
            defaults={
                "document": doc2,
                "section_number": "4.3",
                "title": "Section 4.3 - Service Level Agreement Credits",
                "page_number": 1,
                "category": "Compliance",
                "snippet": "If Monthly Uptime Percentage drops below 99.95%, Customer is eligible for 10% service credit upon written claim within thirty days.",
                "content": "If Monthly Uptime Percentage drops below 99.95%, Customer is eligible for 10% service credit upon written claim within thirty days.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-201",
            defaults={
                "clause": cl2_1,
                "risk_level": "LOW",
                "risk_score": 22,
                "confidence": 94,
                "explanation": "Standard industry SLA credit remedy providing fair recourse for unplanned system unavailability.",
                "business_impact": "Protects recurring budget by offsetting subscription fees during downtime outages.",
                "recommended_action": "Confirm internal monitoring triggers generate alerts when SLA threshold drops below 99.95%.",
                "original_text": cl2_1.snippet,
                "suggested_redline": "Retain 10% SLA credit schedule; add escalation tier to 25% credit for downtime exceeding 4 consecutive hours.",
            }
        )

        cl2_2, _ = Clause.objects.update_or_create(
            id="cl-202",
            defaults={
                "document": doc2,
                "section_number": "8.2",
                "title": "Section 8.2 - Automatic Renewal Window",
                "page_number": 2,
                "category": "Termination",
                "snippet": "Contract automatically renews for 12 months unless non-renewal notice is served 60 days prior to subscription anniversary.",
                "content": "Contract automatically renews for 12 months unless non-renewal notice is served 60 days prior to subscription anniversary.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-202",
            defaults={
                "clause": cl2_2,
                "risk_level": "MEDIUM",
                "risk_score": 52,
                "confidence": 96,
                "explanation": "Contract automatically locks in for another full calendar year unless non-renewal notice is dispatched at least 60 days in advance.",
                "business_impact": "Risk of unwanted budget commitment if procurement evaluation lapses.",
                "recommended_action": "Add calendar alert 75 days prior to anniversary to evaluate renewal.",
                "original_text": cl2_2.snippet,
                "suggested_redline": "Contract shall convert to month-to-month subscription upon initial term completion unless affirmative renewal agreement is executed.",
            }
        )

        cl2_3, _ = Clause.objects.update_or_create(
            id="cl-203",
            defaults={
                "document": doc2,
                "section_number": "10.1",
                "title": "Section 10.1 - Aggregate Liability Cap",
                "page_number": 2,
                "category": "Liability",
                "snippet": "Total aggregate liability of either party under this agreement shall be capped at total fees paid in previous 12 months.",
                "content": "Total aggregate liability of either party under this agreement shall be capped at total fees paid in previous 12 months.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-203",
            defaults={
                "clause": cl2_3,
                "risk_level": "LOW",
                "risk_score": 25,
                "confidence": 97,
                "explanation": "Well-balanced mutual limitation of liability protecting both vendor and enterprise customer.",
                "business_impact": "Limits financial exposure to predictable contract value boundaries.",
                "recommended_action": "Maintain as approved standard language.",
                "original_text": cl2_3.snippet,
                "suggested_redline": "Maintain 12-month trailing fee aggregate liability cap.",
            }
        )

        RiskFinding.objects.update_or_create(
            id="rk-201",
            defaults={
                "document": doc2,
                "clause": cl2_2,
                "title": "Automatic Renewal 60-day Notice Requirement",
                "severity": "MEDIUM",
                "risk_score": 52,
                "confidence": 96,
                "page_number": 2,
                "clause_ref": "Section 8.2",
                "description": "Contract automatically renews for 12 months unless non-renewal notice is served 60 days prior.",
                "business_impact": "Unwanted budget commitment and auto-extension without procurement sign-off.",
                "mitigation": "Configure internal calendar alerts 75 days ahead of renewal deadline.",
            }
        )

        AIAnalysis.objects.update_or_create(
            id="ana-2",
            defaults={
                "document": doc2,
                "score": 32,
                "severity": "LOW",
                "confidence": 96,
                "executive_summary": "Standard cloud subscription terms for managed database streaming services. Balances vendor protections with standard customer SLA remedies and capped liability, though automatic renewal terms require calendar tracking.",
                "key_concerns": [
                    "60-day non-renewal requirement under Section 8.2 triggers automatic 12-month term extension.",
                    "SLA credits limited to 10% under Section 4.3 as sole and exclusive remedy for downtime."
                ],
                "business_impact_summary": "Low general commercial exposure. Moderate procurement rollover risk if non-renewal milestone is missed.",
                "parties": ["Nexus Cloud Systems", "CloudStream Technologies LLC"],
                "effective_date": "January 1, 2026",
                "governing_law": "State of California, USA",
                "status": "completed",
            }
        )

        # =========================================================================
        # DOCUMENT 3: Executive Senior Architect Employment Agreement
        # =========================================================================
        doc3, _ = Document.objects.update_or_create(
            id="doc-3",
            defaults={
                "title": "Executive Senior Architect Employment Agreement",
                "file_name": "Employment_Agreement_VP_Eng.pdf",
                "file_size": "780 KB",
                "page_count": 2,
                "document_type": "Employment Agreement",
                "status": "analyzed",
            }
        )

        cl3_1, _ = Clause.objects.update_or_create(
            id="cl-301",
            defaults={
                "document": doc3,
                "section_number": "7.2",
                "title": "Section 7.2 - Geographic Non-Compete Scope",
                "page_number": 1,
                "category": "Compliance",
                "snippet": "Employee shall not directly or indirectly engage in competitive AI document analysis services worldwide for a period of 12 months following departure.",
                "content": "Employee shall not directly or indirectly engage in competitive AI document analysis services worldwide for a period of 12 months following departure.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-301",
            defaults={
                "clause": cl3_1,
                "risk_level": "HIGH",
                "risk_score": 82,
                "confidence": 93,
                "explanation": "Enforceability of worldwide non-compete covenant is questionable under modern employment statutory guidelines.",
                "business_impact": "Exposes agreement to litigation challenges or total invalidation under current statutory non-compete scrutiny.",
                "recommended_action": "Narrow covenant to direct named competitor organizations and active key accounts.",
                "original_text": cl3_1.snippet,
                "suggested_redline": "Employee agrees not to perform competitive AI services for specific named entities in Schedule A within the New York metropolitan territory for nine (9) months post-departure.",
            }
        )

        cl3_2, _ = Clause.objects.update_or_create(
            id="cl-302",
            defaults={
                "document": doc3,
                "section_number": "9.1",
                "title": "Section 9.1 - Inventions and Discoveries Assignment",
                "page_number": 2,
                "category": "Intellectual Property",
                "snippet": "All inventions, patentable designs, algorithms and discoveries conceived during the employment term belong entirely to the Company.",
                "content": "All inventions, patentable designs, algorithms and discoveries conceived during the employment term belong entirely to the Company.",
            }
        )

        ClauseAnalysis.objects.update_or_create(
            id="ca-302",
            defaults={
                "clause": cl3_2,
                "risk_level": "LOW",
                "risk_score": 20,
                "confidence": 98,
                "explanation": "Standard proprietary invention assignment agreement securing executive IP rights.",
                "business_impact": "Protects corporate patents and core model training datasets.",
                "recommended_action": "Retain standard proprietary assignment schedule.",
                "original_text": cl3_2.snippet,
                "suggested_redline": "Retain standard proprietary invention assignment schedule.",
            }
        )

        RiskFinding.objects.update_or_create(
            id="rk-301",
            defaults={
                "document": doc3,
                "clause": cl3_1,
                "title": "Overly Broad Restrictive Covenant",
                "severity": "HIGH",
                "risk_score": 82,
                "confidence": 93,
                "page_number": 1,
                "clause_ref": "Section 7.2",
                "description": "Global non-compete covenant may be ruled void and unenforceable or trigger legal challenges.",
                "business_impact": "Court invalidation of non-compete and potential exposure of proprietary operational tradecraft.",
                "mitigation": "Tailor geographic scope to direct active client relationships.",
            }
        )

        AIAnalysis.objects.update_or_create(
            id="ana-3",
            defaults={
                "document": doc3,
                "score": 54,
                "severity": "MEDIUM",
                "confidence": 91,
                "executive_summary": "Executive employment agreement featuring intellectual property assignment, confidentiality provisions, 12-month post-employment non-compete, and severance terms.",
                "key_concerns": [
                    "Worldwide geographic non-compete restriction under Section 7.2 faces strict legal unenforceability challenges.",
                    "Overly broad post-employment non-solicitation triggers."
                ],
                "business_impact_summary": "Legal risk of restrictive covenant nullification and potential executive retention friction.",
                "parties": ["DocuSense AI Corp.", "Dr. Elena Rostova"],
                "effective_date": "October 15, 2026",
                "governing_law": "State of New York, USA",
                "status": "completed",
            }
        )

        # =========================================================================
        # SEED SAMPLE CONVERSATION ON DOC-1
        # =========================================================================
        conv1, _ = Conversation.objects.update_or_create(
            id="conv-demo-1",
            defaults={
                "user": demo_user,
                "document": doc1,
                "title": "Liability & Indemnification Review",
            }
        )

        ChatMessage.objects.update_or_create(
            id="msg-demo-1",
            defaults={
                "conversation": conv1,
                "role": "user",
                "content": "Are there any monetary caps on indemnification claims under this agreement?",
                "page_references": [2],
            }
        )

        ChatMessage.objects.update_or_create(
            id="msg-demo-2",
            defaults={
                "conversation": conv1,
                "role": "assistant",
                "content": "Under Section 12.2 (Page 2), neither party's liability for indemnification or confidentiality breaches is subject to any monetary cap or aggregate limitation. This represents an uncapped liability risk.",
                "page_references": [2],
            }
        )

        self.stdout.write(self.style.SUCCESS("Successfully seeded demo agreements (doc-1, doc-2, doc-3) with structured analyses, findings, redlines, and chat sessions!"))

