"""SMS service module with mock mode support.

Supports Aliyun SMS SDK structure. When SMS_MOCK_MODE=true or
sign/template is not configured, falls back to mock mode (logs only).
"""

import json
import os
from typing import Optional

from app import db


class SmsService:
    """SMS service wrapper supporting Aliyun SMS with mock fallback."""

    def __init__(self) -> None:
        self.provider = os.environ.get("SMS_PROVIDER", "aliyun")
        self.access_key_id = os.environ.get("ALIBABA_ACCESS_KEY_ID", "")
        self.access_key_secret = os.environ.get("ALIBABA_ACCESS_KEY_SECRET", "")
        self.sign_name = os.environ.get("ALIBABA_SMS_SIGN_NAME", "")
        self.template_code = os.environ.get("ALIBABA_SMS_TEMPLATE_CODE", "")
        self.mock_mode = os.environ.get("SMS_MOCK_MODE", "true").lower() == "true"

        # If sign or template missing, force mock mode
        if not self.sign_name or not self.template_code:
            self.mock_mode = True

        self._client = None
        if not self.mock_mode:
            self._client = self._create_client()

    def _create_client(self):
        """Create Aliyun SMS client."""
        try:
            from alibabacloud_dysmsapi20170525.client import (
                Client as Dysmsapi20170525Client,
            )
            from alibabacloud_tea_openapi import models as open_api_models

            config = open_api_models.Config(
                access_key_id=self.access_key_id,
                access_key_secret=self.access_key_secret,
            )
            config.endpoint = "dysmsapi.aliyuncs.com"
            return Dysmsapi20170525Client(config)
        except Exception as e:
            print(f"[SMS] Failed to create Aliyun client: {e}")
            self.mock_mode = True
            return None

    def send_sms(
        self,
        phone_number: str,
        template_param: dict,
        template_code: Optional[str] = None,
        sign_name: Optional[str] = None,
    ) -> dict:
        """Send SMS or mock send.

        Args:
            phone_number: Receiver phone number.
            template_param: Template variables dict.
            template_code: Optional override template code.
            sign_name: Optional override sign name.

        Returns:
            Dict with success status and message.
        """
        sign = sign_name or self.sign_name
        template = template_code or self.template_code

        if self.mock_mode or not self._client:
            return self._mock_send(phone_number, sign, template, template_param)

        try:
            from alibabacloud_dysmsapi20170525 import models as dysmsapi_20170525_models
            from alibabacloud_tea_util import models as util_models

            request = dysmsapi_20170525_models.SendSmsRequest(
                phone_numbers=phone_number,
                sign_name=sign,
                template_code=template,
                template_param=json.dumps(template_param, ensure_ascii=False),
            )
            runtime = util_models.RuntimeOptions()
            response = self._client.send_sms_with_options(request, runtime)
            body = response.body

            result = {
                "success": body.code == "OK",
                "code": body.code,
                "message": body.message,
                "request_id": body.request_id,
                "biz_id": body.biz_id,
            }
            self._log_sms(phone_number, template_param, result)
            return result
        except Exception as e:
            error_result = {
                "success": False,
                "code": "Error",
                "message": str(e),
                "request_id": None,
                "biz_id": None,
            }
            self._log_sms(phone_number, template_param, error_result)
            return error_result

    def _mock_send(
        self,
        phone_number: str,
        sign_name: str,
        template_code: str,
        template_param: dict,
    ) -> dict:
        """Mock SMS send - logs to console and returns simulated success."""
        print(f"[SMS MOCK] To: {phone_number}")
        print(f"[SMS MOCK] Sign: {sign_name or '(empty)'}")
        print(f"[SMS MOCK] Template: {template_code or '(empty)'}")
        print(f"[SMS MOCK] Params: {json.dumps(template_param, ensure_ascii=False)}")

        result = {
            "success": True,
            "code": "OK",
            "message": "Mock send success (SMS_MOCK_MODE enabled)",
            "request_id": "mock-request-id",
            "biz_id": "mock-biz-id",
        }
        self._log_sms(phone_number, template_param, result)
        return result

    def _log_sms(self, phone: str, params: dict, result: dict) -> None:
        """Log SMS send attempt to database or file."""
        # Simple console log for now; can be extended to DB table
        status = "SUCCESS" if result.get("success") else "FAILED"
        print(f"[SMS LOG] {status} | Phone: {phone} | Result: {result.get('message')}")


# Convenience functions for common scenarios

def notify_registration_status(
    phone: str, exam_name: str, status: str, review_comment: Optional[str] = None
) -> dict:
    """Notify student about registration status change."""
    service = SmsService()
    params = {"exam_name": exam_name, "status": status}
    if review_comment:
        params["comment"] = review_comment
    return service.send_sms(phone, params)


def notify_exam_reminder(phone: str, exam_name: str, exam_date: str, location: str) -> dict:
    """Notify student about upcoming exam."""
    service = SmsService()
    params = {"exam_name": exam_name, "exam_date": exam_date, "location": location}
    return service.send_sms(phone, params)
