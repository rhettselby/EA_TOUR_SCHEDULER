import json
import os
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.core.cache import cache
from django.views.decorators.http import require_POST
from slack_sdk.signature import SignatureVerifier
from tours.models import Tour, Guest, TourSignup
from .tools.slack_tools import slack_client, build_signups_block, get_slack_name, SIGNUP_ACTION_RESPONSES
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from .tasks import run_slack_agent
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt





@csrf_exempt
def slack_events(request):
    try:
        data = json.loads(request.body)

        # handle Slack's one-time challenge verification
        if data.get('type') == 'url_verification':
            print('sending challenge')
            return JsonResponse({'challenge': data.get('challenge')})

        print('moving past challenge')
        # ignore bot messages to prevent infinite loop
        event = data.get('event', {})
        if event.get('bot_id'):
            return JsonResponse({"error": "avoing response to slack bots message"}, status = 200)

        # ignore edits/deletes, including the bot updating a tour sign-up message
        if event.get('subtype') in ('message_changed', 'message_deleted'):
            return JsonResponse({"message": "ignoring message edit"}, status = 200)

        # only handle actual messages
        if event.get('type') == 'message':
            if not cache.add(f"slack_event:{data.get('event_id')}", True, timeout=60 * 60):
                return JsonResponse({"message": "duplicate event"}, status=200)
            channel = event.get('channel')
            text = event.get('text')
            ts = event.get('ts')
            
            # fire off async task and return 200 immediately
            run_slack_agent.delay(channel, text, ts)

        return JsonResponse({"message": "slack agent called successfuly"}, status = 200)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": str(e)}, status = 500)



def is_from_slack(request):
    """
    Check the X-Slack-Signature header so only Slack can post to this endpoint
    """
    signing_secret = os.environ.get('SLACK_SIGNING_SECRET')
    if not signing_secret:
        print('SLACK_SIGNING_SECRET is not set, rejecting slack request')
        return False
    try:
        return SignatureVerifier(signing_secret).is_valid(
            body=request.body,
            timestamp=request.headers.get('X-Slack-Request-Timestamp'),
            signature=request.headers.get('X-Slack-Signature'),
        )
    except ValueError:
        return False


def tell_user(channel_id, user_id, text):
    """
    Message only the person who clicked (an ephemeral message)
    """
    try:
        slack_client.chat_postEphemeral(channel=channel_id, user=user_id, text=text)
    except Exception as e:
        print(f"Failed to send ephemeral message to {user_id}: {e}")


@csrf_exempt
@require_POST
def slack_interactions(request):
    """
    Slack posts here when someone clicks a button on a tour sign-up message.
    Records their answer and rewrites the message's sign-up list with chat.update.
    """
    # read the raw body before request.POST, the signature is computed over it
    if not is_from_slack(request):
        return HttpResponse(status=403)

    # interactions are form-encoded with the JSON in a "payload" field
    payload = json.loads(request.POST['payload'])
    if payload.get('type') != 'block_actions':
        return HttpResponse(status=200)

    action = payload['actions'][0]
    response = SIGNUP_ACTION_RESPONSES.get(action['action_id'])
    if response is None:
        return HttpResponse(status=200)

    event_id = action['value']
    user = payload['user']
    channel_id = payload['channel']['id']
    message = payload['message']

    try:
        slack_name = get_slack_name(user)

        with transaction.atomic():
            # lock the tour row so clicks on the same message are applied one at a
            # time, and the last chat.update always includes everyone
            tour = Tour.objects.select_for_update().get(event_id=event_id)

            existing = tour.signups.filter(slack_user_id=user['id']).first()
            if existing and existing.response == response:
                # clicking your current answer again takes it back
                existing.delete()
            else:
                TourSignup.objects.update_or_create(
                    tour=tour,
                    slack_user_id=user['id'],
                    defaults={'response': response, 'slack_name': slack_name},
                )

            signups = list(tour.signups.all())
            yes_names = [s.slack_name for s in signups if s.response == 'yes']
            tour.ambassador = ', '.join(yes_names)[:255]
            if tour.status not in ('past_event', 'cancelled'):
                tour.status = 'confirmed' if yes_names else 'message_sent'
            tour.save(update_fields=['ambassador', 'status'])

            # keep the tour details and buttons, only swap in the new sign-up list
            blocks = [
                build_signups_block(signups) if block.get('block_id') == 'tour_signups' else block
                for block in message['blocks']
            ]
            # if this fails the transaction rolls back, so the db never disagrees with slack
            slack_client.chat_update(
                channel=channel_id,
                ts=message['ts'],
                text=message.get('text', ''),
                blocks=blocks,
            )

    except Tour.DoesNotExist:
        tell_user(channel_id, user['id'], "This tour was cancelled or is no longer on the schedule.")
    except Exception as e:
        print(f"Failed to record tour signup for {event_id}: {e}")
        tell_user(channel_id, user['id'], "Something went wrong saving your response, please try again.")

    # slack needs a 200 within 3 seconds or it shows the user an error
    return HttpResponse(status=200)
