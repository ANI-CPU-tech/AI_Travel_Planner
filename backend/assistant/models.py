# assistant/models.py
from django.conf import settings
from django.db import models


class Conversation(models.Model):
    """
    Represents a conversation between a user and the AI assistant.
    If user is authenticated, we link it to the User model.
    Otherwise, we can fallback to a temporary session ID (for anonymous sessions).
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="conversations",
        null=True,
        blank=True
    )
    session_id = models.CharField(max_length=64, blank=True, null=True, db_index=True)
    title = models.CharField(max_length=255, default="New chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    model_name = models.CharField(max_length=128, default="gemini-2.5-flash")

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.title} ({self.user or self.session_id})"


class Message(models.Model):
    """
    A single message in a conversation.
    Stores both user and assistant messages, along with timestamps.
    """
    ROLE_CHOICES = [
        ("user", "User"),
        ("assistant", "Assistant"),
        ("system", "System"),
    ]

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages"
    )
    role = models.CharField(max_length=16, choices=ROLE_CHOICES)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    meta = models.JSONField(blank=True, null=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        short_content = self.content[:40].replace("\n", " ")
        return f"[{self.role}] {short_content}"
