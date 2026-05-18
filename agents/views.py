from tours.models import Tour, Guest
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from .tasks import run_slack_agent
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt





@csrf_exempt
@api_view(['POST'])
@authentication_classes([])
@permission_classes([AllowAny])
def slack_events(request):
    data = request.data

    # Step 1: Handle Slack's one-time challenge verification
    if data.get('type') == 'url_verification':
        return Response({'challenge': data.get('challenge')})

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