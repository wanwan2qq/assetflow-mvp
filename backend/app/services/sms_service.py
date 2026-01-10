"""
SMS service for AssetFlow
Handles SMS verification code sending and validation
"""

import logging
import random
import time
from typing import Dict, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class SMSService:
    """SMS service for sending and validating verification codes"""

    def __init__(self):
        # In-memory storage for verification codes (use Redis in production)
        self._verification_codes: Dict[str, Dict[str, any]] = {}
        self.code_expiry_minutes = 5  # Verification codes expire in 5 minutes

    def generate_verification_code(self) -> str:
        """Generate a 6-digit verification code"""
        return f"{random.randint(100000, 999999)}"

    async def send_verification_code(self, phone: str) -> bool:
        """
        Send verification code to phone number
        In development, just print the code to console
        In production, integrate with SMS provider (Aliyun, Tencent Cloud, etc.)
        """
        try:
            # Generate verification code
            code = self.generate_verification_code()
            
            # Store code with expiry timestamp
            self._verification_codes[phone] = {
                "code": code,
                "timestamp": time.time(),
                "attempts": 0
            }

            if settings.ENVIRONMENT == "development":
                # In development, print the code to console
                logger.info(f"📱 SMS验证码发送到 {phone}: {code}")
                print(f"\n🔐 开发环境 - SMS验证码")
                print(f"📱 手机号: {phone}")
                print(f"🔢 验证码: {code}")
                print(f"⏰ 有效期: {self.code_expiry_minutes}分钟")
                print("-" * 40)
                return True
            else:
                # In production, integrate with SMS provider
                # TODO: Implement actual SMS sending
                # Example integrations:
                # - Aliyun SMS: https://help.aliyun.com/product/44282.html
                # - Tencent Cloud SMS: https://cloud.tencent.com/product/sms
                # - Twilio: https://www.twilio.com/sms
                logger.warning("Production SMS sending not implemented yet")
                return False

        except Exception as e:
            logger.error(f"Failed to send SMS to {phone}: {e}")
            return False

    async def verify_code(self, phone: str, code: str) -> bool:
        """
        Verify the SMS code for a phone number
        """
        try:
            # In development, accept common test codes
            if settings.ENVIRONMENT == "development":
                test_codes = ["123456", "000000", "111111", "888888", "666666"]
                if code in test_codes:
                    logger.info(f"✅ 开发环境测试验证码验证成功: {phone} - {code}")
                    return True
            
            stored_data = self._verification_codes.get(phone)
            
            if not stored_data:
                logger.warning(f"No verification code found for phone: {phone}")
                return False

            # Check if code has expired
            current_time = time.time()
            code_age_minutes = (current_time - stored_data["timestamp"]) / 60
            
            if code_age_minutes > self.code_expiry_minutes:
                logger.warning(f"Verification code expired for phone: {phone}")
                # Clean up expired code
                del self._verification_codes[phone]
                return False

            # Check attempts limit (prevent brute force)
            if stored_data["attempts"] >= 3:
                logger.warning(f"Too many verification attempts for phone: {phone}")
                del self._verification_codes[phone]
                return False

            # Verify the code
            if stored_data["code"] == code:
                logger.info(f"✅ SMS验证码验证成功: {phone}")
                # Mark as used but keep for rate limiting (will be cleaned up by expiry)
                stored_data["used"] = True
                stored_data["used_at"] = current_time
                return True
            else:
                # Increment attempt counter
                stored_data["attempts"] += 1
                logger.warning(f"❌ SMS验证码错误: {phone}, 尝试次数: {stored_data['attempts']}")
                return False

        except Exception as e:
            logger.error(f"Failed to verify SMS code for {phone}: {e}")
            return False

    def cleanup_expired_codes(self):
        """Clean up expired verification codes"""
        current_time = time.time()
        expired_phones = []
        
        for phone, data in self._verification_codes.items():
            code_age_minutes = (current_time - data["timestamp"]) / 60
            if code_age_minutes > self.code_expiry_minutes:
                expired_phones.append(phone)
        
        for phone in expired_phones:
            del self._verification_codes[phone]
            logger.info(f"Cleaned up expired verification code for: {phone}")

    async def request_verification_code(self, phone: str) -> Dict[str, any]:
        """
        Request a verification code for phone number
        Returns status and message
        """
        # Check if there's a recent code for this phone (rate limiting)
        stored_data = self._verification_codes.get(phone)
        if stored_data:
            current_time = time.time()
            code_age_seconds = current_time - stored_data["timestamp"]
            
            # Rate limit: only allow new code every 60 seconds
            if code_age_seconds < 60:
                remaining_seconds = int(60 - code_age_seconds)
                return {
                    "success": False,
                    "message": f"请等待 {remaining_seconds} 秒后再次发送验证码",
                    "code": "RATE_LIMITED"
                }
            
            # If code was used, require longer wait time (5 minutes)
            if stored_data.get("used") and code_age_seconds < 300:
                remaining_seconds = int(300 - code_age_seconds)
                return {
                    "success": False,
                    "message": f"验证码已使用，请等待 {remaining_seconds} 秒后再次发送",
                    "code": "RATE_LIMITED"
                }

        # Send verification code
        success = await self.send_verification_code(phone)
        
        if success:
            return {
                "success": True,
                "message": "验证码已发送",
                "code": "SMS_SENT"
            }
        else:
            return {
                "success": False,
                "message": "验证码发送失败，请稍后重试",
                "code": "SMS_FAILED"
            }


# Global SMS service instance
sms_service = SMSService()