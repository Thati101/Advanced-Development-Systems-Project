# chat/admin.py
from django.contrib import admin
from django.contrib.auth import get_user_model
from .models import Chat, Message
from django.urls import path
from django.http import HttpResponseRedirect

User = get_user_model()

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat_participants', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('participants__username',)
    filter_horizontal = ('participants',)

    def chat_participants(self, obj):
        return ", ".join([user.username for user in obj.participants.all()])
    chat_participants.short_description = 'Participants'

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'chat', 'sender', 'text', 'timestamp')
    list_filter = ('timestamp',)
    search_fields = ('text', 'sender__username', 'chat__participants__username')
    autocomplete_fields = ('chat', 'sender')

# Add this inside your component, e.g. above the chat list
def startAdminChat(request):
    # Logic to start chat with admin
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))

urlpatterns = [
    path('admin/chat/', admin.site.urls),
    path('admin/chat/start/', startAdminChat, name='start_admin_chat'),
]
