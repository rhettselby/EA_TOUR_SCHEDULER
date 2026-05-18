import json
from django.http import HttpResponse
from tours.models import Tour, Guest
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from .tasks import run_slack_agent
from rest_framework.permissions import AllowAny





@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def slack_events(request):
    data = json.loads(request.body)

    # Step 1: Handle Slack's one-time challenge verification
    if data.get('type') == 'url_verification':
        print('sending challenge')
        return HttpResponse(data.get('challenge'), content_type="text/plain", status=200)

    print('moving past challenge')
    # Step 2: Ignore bot messages to prevent infinite loop
    event = data.get('event', {})
    if event.get('bot_id'):
        return Response(status=200)

    # Step 3: Only handle actual messages
    if event.get('type') == 'message':
        channel = event.get('channel')
        text = event.get('text')
        ts = event.get('ts')
        
        # Step 4: Fire off async task and return 200 immediately
        run_slack_agent.delay(channel, text, ts)

    return Response(status=200)