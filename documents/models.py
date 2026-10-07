from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

User = settings.AUTH_USER_MODEL


class Document(models.Model):
    """
    Represents an enterprise legal document / contract uploaded for intelligent analysis.
    """
    DOCUMENT_TYPES = [
        ('Master Services Agreement', 'Master Services Agreement'),
        ('SaaS Vendor Agreement', 'SaaS Vendor Agreement'),
        ('Employment Agreement', 'Employment Agreement'),
        ('Non-Disclosure Agreement', 'Non-Disclosure Agreement'),
        ('Service Level Agreement', 'Service Level Agreement'),
        ('Technical Specification', 'Technical Specification'),
    ]

    STATUS_CHOICES = [
        ('uploaded', 'Uploaded'),
        ('processing', 'Processing'),
        ('analyzed', 'Analyzed'),
        ('failed', 'Failed'),
    ]

    # Supports custom external IDs like "doc-1" as well as standard auto-IDs
    id = models.CharField(max_length=64, primary_key=True, editable=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True,
        help_text="Authenticated owner of this document."
    )
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/', null=True, blank=True)
    file_name = models.CharField(max_length=255, blank=True)
    file_size = models.CharField(max_length=64, blank=True, default='1.0 MB')
    page_count = models.PositiveIntegerField(default=1)
    document_type = models.CharField(
        max_length=64,
        choices=DOCUMENT_TYPES,
        default='Master Services Agreement'
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default='uploaded')
    extracted_text = models.TextField(blank=True, default='')
    extracted_pages = models.JSONField(blank=True, default=list)  # [{'page_number': 1, 'text': '...'}]
    extraction_error = models.TextField(blank=True, default='')
    extracted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['document_type']),
        ]

    def __str__(self):
        return f"{self.title} ({self.id})"


# Clean up physical file when Document record is deleted
from django.db.models.signals import post_delete
from django.dispatch import receiver


@receiver(post_delete, sender=Document)
def delete_document_file_on_delete(sender, instance, **kwargs):
    if instance.file:
        try:
            # Delete without saving model since it's already deleted
            instance.file.delete(save=False)
        except Exception:
            pass


class Clause(models.Model):
    """
    Represents an individual clause or contractual section extracted from a Document.
    """
    id = models.CharField(max_length=64, primary_key=True, editable=True)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name='clauses')
    section_number = models.CharField(max_length=64, blank=True)
    title = models.CharField(max_length=255)
    page_number = models.PositiveIntegerField(default=1)
    category = models.CharField(max_length=64, default='Liability')
    snippet = models.TextField(blank=True)
    content = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['page_number', 'section_number']
        indexes = [
            models.Index(fields=['document', 'page_number']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f"{self.title} - {self.document.id}"


class Conversation(models.Model):
    """
    Represents a scoped chat session on a specific Document for an authenticated user.
    """
    id = models.CharField(max_length=64, primary_key=True, editable=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='conversations',
        null=True,
        blank=True,
        help_text="User who initiated this conversation."
    )
    document = models.ForeignKey(
        Document,
        on_delete=models.CASCADE,
        related_name='conversations',
        help_text="Document being queried."
    )
    title = models.CharField(max_length=255, default="Contract Inquiry")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['document', '-updated_at']),
            models.Index(fields=['user', '-updated_at']),
        ]

    def __str__(self):
        return f"Chat: {self.title} ({self.document.id})"


class ChatMessage(models.Model):
    """
    Represents an individual chat message in a Document conversation.
    """
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
        ('system', 'System'),
    ]

    id = models.CharField(max_length=64, primary_key=True, editable=True)
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES, default='user')
    content = models.TextField()
    page_references = models.JSONField(default=list, blank=True)  # [1, 2, 3] or [{'page': 2, 'snippet': '...'}]
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
        ]

    def __str__(self):
        return f"[{self.role}] {self.content[:40]}... ({self.conversation.id})"

