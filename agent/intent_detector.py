"""
Intent and Entity Detection for Airline Disruption Resolution (AirResolve).

Identifies user intent, sentiment triggers, and domain entities from natural language.
Supports rich phrase variations, regex matching, and semantic intent classification.
"""

from enum import Enum
import re
from typing import Any, Dict, List, Optional, Tuple


class UserIntent(str, Enum):
    GREETING = "GREETING"
    CHECK_STATUS = "CHECK_STATUS"
    CHECK_BENEFITS = "CHECK_BENEFITS"
    REQUEST_REFUND = "REQUEST_REFUND"
    REQUEST_REBOOKING = "REQUEST_REBOOKING"
    REQUEST_HOTEL = "REQUEST_HOTEL"
    REQUEST_UPGRADE = "REQUEST_UPGRADE"
    REQUEST_HIGHER_FARE_REBOOKING = "REQUEST_HIGHER_FARE_REBOOKING"
    LEGAL_OR_FORMAL_COMPLAINT = "LEGAL_OR_FORMAL_COMPLAINT"
    ALTERNATE_PAYMENT_REFUND = "ALTERNATE_PAYMENT_REFUND"
    NON_AIRLINE_DISRUPTION = "NON_AIRLINE_DISRUPTION"
    EXPRESS_FRUSTRATION = "EXPRESS_FRUSTRATION"
    GENERAL_INQUIRY = "GENERAL_INQUIRY"
    UNKNOWN = "UNKNOWN"


class IntentDetector:
    """
    Robust pattern-based and semantic intent classifier for airline disruption conversations.
    """

    # Intent regex patterns
    PATTERNS: Dict[UserIntent, List[str]] = {
        UserIntent.LEGAL_OR_FORMAL_COMPLAINT: [
            r"\b(legal\s+action|lawyer|attorney|sue|court|lawsuit)\b",
            r"\b(formal\s+complaint|file\s+a\s+complaint|regulatory\s+complaint)\b",
            r"\b(consumer\s+court|consumer\s+forum|dgca\s+complaint)\b",
        ],
        UserIntent.ALTERNATE_PAYMENT_REFUND: [
            r"\b(different\s+card|another\s+account|cash\s+instead|different\s+payment|other\s+bank)\b",
            r"\b(send\s+to\s+another|transfer\s+to\s+my\s+other|new\s+account)\b",
        ],
        UserIntent.NON_AIRLINE_DISRUPTION: [
            r"\b(i\s+woke\s+up\s+late|missed\s+my\s+flight|traffic\s+jam|cab\s+broke\s+down)\b",
            r"\b(personal\s+emergency|my\s+fault|got\s+stuck\s+in\s+traffic)\b",
        ],
        UserIntent.REQUEST_UPGRADE: [
            r"\b(business\s+class|upgrade|first\s+class|club\s+class|better\s+seats?)\b",
            r"\b(upgrade\s+me|complimentary\s+upgrade|free\s+upgrade)\b",
        ],
        UserIntent.REQUEST_HIGHER_FARE_REBOOKING: [
            r"\b(more\s+expensive\s+flight|higher\s+fare|different\s+flight\s+instead\s+of\s+waiting)\b",
            r"\b(different,\s*higher-fare|higher-fare\s+flight|fare\s+difference)\b",
            r"\b(move\s+me\s+onto\s+a\s+different\s+flight|switch\s+to\s+another\s+flight)\b",
        ],
        UserIntent.REQUEST_HOTEL: [
            r"\b(hotel|accommodation|room|stay|somewhere\s+to\s+sleep|place\s+to\s+sleep|sleep|bed)\b",
            r"\b(need\s+a\s+hotel|place\s+to\s+rest|hotel\s+stay|full\s+night'?s?\s+stay|overnight)\b",
        ],
        UserIntent.REQUEST_REFUND: [
            r"\b(give\s+me\s+my\s+money\s+back|money\s+back|full\s+refund|refund\s+my\s+ticket)\b",
            r"\b(want\s+a?\s*refund|cancel\s+and\s+refund|reimburse|cash\s+refund)\b",
            r"\b(claim\s+refund|return\s+my\s+fare|get\s+my\s+money)\b",
        ],
        UserIntent.REQUEST_REBOOKING: [
            r"\b(put\s+me\s+on\s+another\s+flight|rebook|next\s+flight|reschedule)\b",
            r"\b(change\s+flight|alternate\s+flight|next\s+available)\b",
        ],
        UserIntent.CHECK_BENEFITS: [
            r"\b(what\s+do\s+i\s+get|what\s+are\s+my\s+benefits|compensation|voucher|meal)\b",
            r"\b(lounge|am\s+i\s+entitled|what\s+can\s+you\s+give|delay\s+compensation)\b",
        ],
        UserIntent.CHECK_STATUS: [
            r"\b(flight\s+status|why\s+is\s+my\s+flight|status\s+of\s+flight|what\s+happened)\b",
            r"\b(is\s+it\s+cancelled|how\s+long\s+is\s+the\s+delay|delayed\s+by)\b",
        ],
        UserIntent.EXPRESS_FRUSTRATION: [
            r"\b(furious|angry|unacceptable|ridiculous|useless|terrible|ruined)\b",
            r"\b(frustrated|disaster|horrible\s+service|screwed\s+up)\b",
        ],
        UserIntent.GREETING: [
            r"^(hi|hello|hey|good\s+morning|good\s+afternoon|good\s+evening)\b",
        ],
    }

    def detect_intent(self, text: str) -> Tuple[UserIntent, float, List[UserIntent]]:
        """
        Detect primary intent and secondary intent signals from text.
        Returns: (primary_intent, confidence, all_detected_intents)
        """
        clean_text = text.lower().strip()
        matched_intents: List[UserIntent] = []

        # Priority 1: Legal action or formal complaints ALWAYS takes topmost priority
        if self._matches(clean_text, UserIntent.LEGAL_OR_FORMAL_COMPLAINT):
            matched_intents.append(UserIntent.LEGAL_OR_FORMAL_COMPLAINT)

        # Check all other categories
        for intent, patterns in self.PATTERNS.items():
            if intent == UserIntent.LEGAL_OR_FORMAL_COMPLAINT:
                continue
            if self._matches(clean_text, intent):
                if intent not in matched_intents:
                    matched_intents.append(intent)

        # Also detect compound requests: e.g. "full cash refund plus a free upgrade to business class"
        if not matched_intents:
            return UserIntent.GENERAL_INQUIRY, 0.5, [UserIntent.GENERAL_INQUIRY]

        primary = matched_intents[0]
        confidence = 0.95 if len(matched_intents) == 1 else 0.85
        return primary, confidence, matched_intents

    def _matches(self, text: str, intent: UserIntent) -> bool:
        patterns = self.PATTERNS.get(intent, [])
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract key entities such as fare amounts, flight numbers, PNRs, duration, and stay type.
        """
        entities: Dict[str, Any] = {
            "fare_difference_inr": None,
            "full_night_requested": False,
            "business_upgrade_requested": False,
            "refund_method_requested": "original",
            "is_furious": False,
            "mentioned_pnr": None,
            "mentioned_flight": None,
        }

        text_lower = text.lower()

        # Fare difference extraction (e.g. ₹2,000, 2000, 2,000 rs, rs 2000)
        fare_patterns = [
            r"₹\s*([0-9,]+)",
            r"rs\.?\s*([0-9,]+)",
            r"inr\s*([0-9,]+)",
            r"([0-9,]+)\s*(?:rupees|inr|rs)",
            r"fare\s+difference\s+(?:of\s+)?(?:is\s+)?₹?\s*([0-9,]+)",
        ]
        for pat in fare_patterns:
            m = re.search(pat, text, re.IGNORECASE)
            if m:
                amount_str = m.group(1).replace(",", "")
                try:
                    entities["fare_difference_inr"] = float(amount_str)
                    break
                except ValueError:
                    pass

        # Full night hotel stay entity
        if re.search(r"\b(full\s+night'?s?|whole\s+night|entire\s+night|overnight)\b", text_lower):
            entities["full_night_requested"] = True

        # Business class / upgrade entity
        if re.search(r"\b(business\s+class|upgrade|first\s+class)\b", text_lower):
            entities["business_upgrade_requested"] = True

        # Alternate payment method
        if re.search(r"\b(different\s+card|another\s+account|cash\s+instead|different\s+payment)\b", text_lower):
            entities["refund_method_requested"] = "alternate"

        # Furious / emotional signal
        if re.search(r"\b(furious|extremely\s+angry|screwed|unacceptable|livid)\b", text_lower):
            entities["is_furious"] = True

        # PNR extraction (e.g. SK4821X, TR1190B, WL7742)
        pnr_match = re.search(r"\b([A-Z]{2}[0-9]{4}[A-Z]|[A-Z]{2}[0-9]{4})\b", text)
        if pnr_match:
            entities["mentioned_pnr"] = pnr_match.group(1)

        # Flight number extraction (e.g. SK-204, SK-118, SK-305)
        flight_match = re.search(r"\b(SK-?[0-9]{3})\b", text, re.IGNORECASE)
        if flight_match:
            entities["mentioned_flight"] = flight_match.group(1).upper()

        return entities
