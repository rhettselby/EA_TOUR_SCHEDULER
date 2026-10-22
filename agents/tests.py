import json
import time
from datetime import timedelta
from unittest.mock import patch
from urllib.parse import urlencode

from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from slack_sdk.errors import SlackApiError
from slack_sdk.signature import SignatureVerifier

from tours.models import Tour, TourSignup
from agents.tools.slack_tools import slack_client, build_tour_signup_blocks


SIGNING_SECRET = "test-signing-secret"


@override_settings(SECURE_SSL_REDIRECT=False)
@patch.dict("os.environ", {"SLACK_SIGNING_SECRET": SIGNING_SECRET})
class SlackInteractionsTests(TestCase):

    def setUp(self):
        start = timezone.now() + timedelta(days=2)
        self.tour = Tour.objects.create(
            event_id="123_456",
            start_dt=start,
            end_dt=start + timedelta(hours=1),
            number_of_guests=2,
            status="message_sent",
        )
        self.text = "<!channel> You have an upcoming tour on Monday (10/19) at 10:00 AM."
        self.message = {
            "ts": "1700000000.000100",
            "text": self.text,
            "blocks": build_tour_signup_blocks(self.text, self.tour.event_id),
        }

        patchers = {
            "chat_update": patch.object(slack_client, "chat_update"),
            "chat_postEphemeral": patch.object(slack_client, "chat_postEphemeral"),
            "users_info": patch.object(slack_client, "users_info"),
        }
        self.mocks = {name: p.start() for name, p in patchers.items()}
        for p in patchers.values():
            self.addCleanup(p.stop)
        self.names = {"U1": "Alice Smith", "U2": "Bob Lee"}
        self.mocks["users_info"].side_effect = lambda user: {
            "user": {"profile": {"real_name": self.names[user]}}
        }

    def click(self, user_id, action_id, event_id=None, secret=SIGNING_SECRET):
        payload = {
            "type": "block_actions",
            "user": {"id": user_id, "username": user_id.lower(), "name": user_id.lower()},
            "channel": {"id": "C123"},
            "message": self.message,
            "actions": [{"action_id": action_id, "value": event_id or self.tour.event_id}],
        }
        body = urlencode({"payload": json.dumps(payload)})
        timestamp = str(int(time.time()))
        signature = SignatureVerifier(secret).generate_signature(timestamp=timestamp, body=body)
        response = self.client.post(
            reverse("agents:slack_interactions"),
            data=body,
            content_type="application/x-www-form-urlencoded",
            HTTP_X_SLACK_REQUEST_TIMESTAMP=timestamp,
            HTTP_X_SLACK_SIGNATURE=signature,
        )
        # the next click sees the message as slack last rendered it
        if self.mocks["chat_update"].called:
            self.message = {**self.message, "blocks": self.mocks["chat_update"].call_args.kwargs["blocks"]}
        return response

    def signups_text(self):
        blocks = self.mocks["chat_update"].call_args.kwargs["blocks"]
        return next(b for b in blocks if b["block_id"] == "tour_signups")["text"]["text"]

    def test_rejects_bad_signature(self):
        response = self.click("U1", "tour_signup_yes", secret="wrong-secret")
        self.assertEqual(response.status_code, 403)
        self.assertFalse(TourSignup.objects.exists())

    def test_rejects_when_signing_secret_unset(self):
        with patch.dict("os.environ", {"SLACK_SIGNING_SECRET": ""}):
            response = self.click("U1", "tour_signup_yes")
        self.assertEqual(response.status_code, 403)

    def test_yes_bolds_name_and_confirms_tour(self):
        response = self.click("U1", "tour_signup_yes")

        self.assertEqual(response.status_code, 200)
        self.assertIn("*Alice Smith*", self.signups_text())
        update = self.mocks["chat_update"].call_args.kwargs
        self.assertEqual((update["channel"], update["ts"]), ("C123", "1700000000.000100"))
        self.assertEqual(
            [b["block_id"] for b in update["blocks"]],
            ["tour_details", "tour_signups", "tour_signup_actions"],
        )
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.status, "confirmed")
        self.assertEqual(self.tour.ambassador, "Alice Smith")

    def test_no_is_listed_without_bold(self):
        self.click("U1", "tour_signup_yes")
        self.click("U2", "tour_signup_no")

        text = self.signups_text()
        self.assertIn("Taking it: *Alice Smith*", text)
        self.assertIn("Can't make it: Bob Lee", text)
        self.assertNotIn("*Bob Lee*", text)

    def test_clicking_same_answer_again_takes_it_back(self):
        self.click("U1", "tour_signup_yes")
        self.click("U1", "tour_signup_yes")

        self.assertFalse(TourSignup.objects.exists())
        self.assertIn("No one has signed up yet", self.signups_text())
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.status, "message_sent")
        self.assertEqual(self.tour.ambassador, "")

    def test_switching_answer_updates_existing_signup(self):
        self.click("U1", "tour_signup_yes")
        self.click("U1", "tour_signup_no")

        signup = TourSignup.objects.get()
        self.assertEqual(signup.response, "no")
        self.assertNotIn("Taking it", self.signups_text())

    def test_unknown_tour_tells_user_privately(self):
        response = self.click("U1", "tour_signup_yes", event_id="cancelled_tour")

        self.assertEqual(response.status_code, 200)
        self.mocks["chat_update"].assert_not_called()
        self.assertIn("cancelled", self.mocks["chat_postEphemeral"].call_args.kwargs["text"])

    def test_failed_slack_update_rolls_back_signup(self):
        self.mocks["chat_update"].side_effect = SlackApiError("boom", response={"ok": False})

        response = self.click("U1", "tour_signup_yes")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(TourSignup.objects.exists())
        self.tour.refresh_from_db()
        self.assertEqual(self.tour.status, "message_sent")
        self.mocks["chat_postEphemeral"].assert_called_once()

    def test_falls_back_to_username_without_users_read_scope(self):
        self.mocks["users_info"].side_effect = SlackApiError("missing_scope", response={"ok": False})

        self.click("U1", "tour_signup_yes")

        self.assertEqual(TourSignup.objects.get().slack_name, "u1")


@override_settings(SECURE_SSL_REDIRECT=False)
class SlackEventsTests(TestCase):

    @patch("agents.views.run_slack_agent")
    def test_ignores_message_edits(self, run_slack_agent):
        event = {"type": "message", "subtype": "message_changed", "channel": "C123", "message": {"bot_id": "B1"}}
        response = self.client.post(
            reverse("agents:slack_events"),
            data=json.dumps({"event": event, "event_id": "Ev1"}),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        run_slack_agent.delay.assert_not_called()
