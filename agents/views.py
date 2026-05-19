import json
from django.http import HttpResponse, JsonResponse
from tours.models import Tour, Guest
from rest_framework.decorators import api_view, authentication_classes, permission_classes
from rest_framework.response import Response
from .tasks import run_slack_agent
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt





@csrf_exempt
def slack_events(request):
    try:
        data = json.loads(request.body)

        # Step 1: Handle Slack's one-time challenge verification
        if data.get('type') == 'url_verification':
            print('sending challenge')
            return JsonResponse({'challenge': data.get('challenge')})

        print('moving past challenge')
        # Step 2: Ignore bot messages to prevent infinite loop
        event = data.get('event', {})
        if event.get('bot_id'):
            return JsonResponse(status=200)

        # Step 3: Only handle actual messages
        if event.get('type') == 'message':
            channel = event.get('channel')
            text = event.get('text')
            ts = event.get('ts')
            
            # Step 4: Fire off async task and return 200 immediately
            run_slack_agent.delay(channel, text, ts)

        return Response(status=200)
    except Exception as e:
        print(str(e))
        return JsonResponse({"error": str(e)}, status = 500)