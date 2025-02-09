from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import ChessLobby, User, ActiveGames, Challenge, Notification

@receiver(post_save, sender=ChessLobby)
def notify_game_update_on_save(sender, instance, **kwargs):
    channel_layer = get_channel_layer()

    white_user = User.objects.filter(id=instance.white_id).first()
    white_username = white_user.username if white_user else 'Anon'
    
    black_user = User.objects.filter(id=instance.black_id).first()
    black_username = black_user.username if black_user else 'Anon'
    
    active_game = ActiveGames.objects.filter(active_game_id=instance.lobby_id).first()
    
    start_time = str(active_game.start_time) if active_game else None
    is_ready = start_time is None and instance.initiator_connected and instance.opponent_connected
    multiplayer = not instance.computer_game and not instance.solo_game and not instance.private

    async_to_sync(channel_layer.group_send)(
        'game_updates',
        {
            'type': 'send_update',
            'data': {
                'action': 'save',
                'id': str(instance.lobby_id),
                'white_username': white_username,
                'black_username': black_username,
                'gametype': instance.gametype,
                'start_time': start_time,
                'new_multiplayer': is_ready and multiplayer,
                "initiator_name": instance.initiator_name,
                "game_uuid": str(instance.lobby_id),
                "side": "white" if instance.white_id is None else "black",
                "game_type": instance.gametype,
                "subvariant": instance.subvariant,
                "ranked": instance.match_type,
                "initiator_elo": instance.white_rank_start if instance.initiator_color == 'white' else instance.black_rank_start,
                'open_game': multiplayer and instance.is_open,
            }
        }
    )

@receiver(post_delete, sender=ChessLobby)
def notify_game_update_on_delete(sender, instance, **kwargs):
    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        'game_updates',
        {
            'type': 'send_update',
            'data': {
                'action': 'delete',
                'id': str(instance.lobby_id)
            }
        }
    )

@receiver(post_save, sender=Challenge)
def notify_challenge_update_on_save(sender, instance, **kwargs):
    channel_layer = get_channel_layer()

    if instance.challenge_accepted is None:
        accepted = None
    elif instance.challenge_accepted:
        accepted = "accepted"
    else:
        accepted = "denied"

    message = {'log': accepted}
    if instance.game_id is not None and accepted == "accepted":
        message.update({'url': f'/play/{instance.game_id}'})

    if accepted is not None:
        async_to_sync(channel_layer.group_send)(
            f"challenge_{str(instance.challenge_id)}",
            {
                'type': 'chat.message',
                'message': message
            }
        )

@receiver(post_save, sender=Notification)
def notify_notification_update_on_save(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    username = instance.user.username
    async_to_sync(channel_layer.group_send)(
        f'notifications_{username}',
        {
            'type': 'send_update',
            'data': {
                'action': 'save',
                'notification_id': str(instance.notification_id),
                'message_id': str(instance.message.message_id),
                'created_at': instance.created_at.isoformat(),
                'is_seen': instance.is_seen,
                'sender_username': instance.message.sender.username,
                'subject': instance.message.subject
            }
        }
    )

@receiver(post_delete, sender=Notification)
def notify_notification_update_on_delete(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    username = instance.user.username
    async_to_sync(channel_layer.group_send)(
        f'notifications_{username}',
        {
            'type': 'send_update',
            'data': {
                'action': 'delete',
                'notification_id': str(instance.notification_id)
            }
        }
    )