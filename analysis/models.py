from django.db import models
from documents.models import Document, Clause


class AIAnalysis(models.Model):
    """
    Represents the overall AI contract assessment for a Document.
    """
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    STATUS_CHOICES = [
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    id = models.CharField(max_length=64, primary_key=True, editable=True)
    document = models.OneToOneField(Document, on_delete=models.CASCADE, related_name='analysis')
    contract_type = models.CharField(max_length=128, blank=True, default='')
    score = models.IntegerField(default=50)  # 0 to 100
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default='MEDIUM')
    confidence = models.IntegerField(default=94)  # 0 to 100
    executive_summary = models.TextField(blank=True)
    key_concerns = models.JSONField(default=list, blank=True)
    business_impact_summary = models.TextField(blank=True)
    parties = models.JSONField(default=list, blank=True)
    governing_law = models.CharField(max_length=255, blank=True)
    effective_date = models.CharField(max_length=128, blank=True)
    analysis_data = models.JSONField(default=dict, blank=True)  # Full structured analysis (clauses, risks, obligations, terms, missing)
    model_name = models.CharField(max_length=64, blank=True, default='docusense-ai-legal-v1')
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='completed')
    analyzed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-analyzed_at']
        indexes = [
            models.Index(fields=['document']),
            models.Index(fields=['severity']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Analysis for {self.document.id} (Score: {self.score})"

    @property
    def findings_breakdown(self):
        """
        Dynamically calculate counts of risk findings across severity tiers.
        """
        findings = self.document.risks.all()
        return {
            'total': findings.count(),
            'critical': findings.filter(severity='CRITICAL').count(),
            'high': findings.filter(severity='HIGH').count(),
            'medium': findings.filter(severity='MEDIUM').count(),
            'low': findings.filter(severity='LOW').count(),
        }


class RiskFinding(models.Model):
    """
    Represents an empirical legal or operational risk factor detected by the AI engine.
    """
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    id = models.CharField(max_length=64, primary_key=True, editable=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='risks')
    clause = models.ForeignKey(Clause, on_delete=models.SET_NULL, null=True, blank=True, related_name='risks')
    title = models.CharField(max_length=255)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default='MEDIUM')
    risk_score = models.IntegerField(default=50)
    confidence = models.IntegerField(default=94)
    page_number = models.PositiveIntegerField(default=1)
    clause_ref = models.CharField(max_length=64, blank=True)
    description = models.TextField()
    business_impact = models.TextField(blank=True)
    mitigation = models.TextField(blank=True)  # recommended action
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-risk_score', 'page_number']
        indexes = [
            models.Index(fields=['document', '-risk_score']),
            models.Index(fields=['severity']),
            models.Index(fields=['page_number']),
        ]

    def __str__(self):
        return f"{self.title} [{self.severity}] - {self.document.id}"


class ClauseAnalysis(models.Model):
    """
    Represents detailed AI analysis, risk rationale, impact, and suggested redline for a specific Clause.
    """
    SEVERITY_CHOICES = [
        ('CRITICAL', 'Critical'),
        ('HIGH', 'High'),
        ('MEDIUM', 'Medium'),
        ('LOW', 'Low'),
    ]

    id = models.CharField(max_length=64, primary_key=True, editable=True)
    clause = models.OneToOneField(Clause, on_delete=models.CASCADE, related_name='clause_analysis')
    risk_level = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default='LOW')
    risk_score = models.IntegerField(default=30)
    confidence = models.IntegerField(default=95)
    explanation = models.TextField(blank=True)  # Why it is risky
    business_impact = models.TextField(blank=True)
    recommended_action = models.TextField(blank=True)
    original_text = models.TextField(blank=True)
    suggested_redline = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['risk_level']),
        ]

    def __str__(self):
        return f"Analysis: {self.clause.title} ({self.risk_level})"
