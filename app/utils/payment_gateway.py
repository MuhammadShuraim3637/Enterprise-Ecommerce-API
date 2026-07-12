import uuid
from decimal import Decimal

class DummyPaymentGateway:
    @staticmethod
    def process_transaction(amount: Decimal, card_number: str) -> dict:
        """
        Simulates payment processing.
        Card starting with '5555' will trigger a hard failure.
        """
        if card_number.replace(" ", "").startswith("5555"):
            return {
                "success": False,
                "transaction_id": None,
                "error": "Card declined by issuing bank."
            }
        
        # Success state simulation
        return {
            "success": True,
            "transaction_id": f"txn_{uuid.uuid4().hex[:12]}",
            "error": None
        }