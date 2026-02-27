import random
import uuid

class MockBankAPI:
    @staticmethod
    def get_transaction_status(txn_id, amount=0, receiver_id=""):
        # Mocks a bank status check based on the transaction amount
        if amount % 2 == 0 and amount != 0:
            # Multiples of 2 (e.g. 2, 4, 6, 8, 10): Money was NEVER debited
            return {"debited": False, "credited": False, "status": "FAILED"}
        elif amount % 5 == 0 and amount != 0:
            # Multiples of 5 (odd: 5, 15...): Money debited, not credited to merchant yet
            return {"debited": True, "credited": False, "status": "PENDING_CREDIT"}
        else:
            # Any other amount: Success
            return {"debited": True, "credited": True, "status": "SUCCESS"}
            
        # Default behavior: Randomize for demo purposes
        statuses = [
            {"debited": True, "credited": True, "status": "SUCCESS"},
            {"debited": True, "credited": False, "status": "PENDING_CREDIT"},
            {"debited": False, "credited": False, "status": "FAILED"}
        ]
        return random.choice(statuses)

    @staticmethod
    def initiate_refund(txn_id, amount):
        # Mocks refund initiation
        ref_id = f"REF-{str(uuid.uuid4())[:8]}"
        return {"refund_id": ref_id, "status": "REFUND_INITIATED", "amount": amount}


class MockMerchantAPI:
    @staticmethod
    def get_merchant_transaction_status(merchant_txn_id, amount=0, receiver_id=""):
        # Mocks checking merchant's end based on amount
        if amount % 5 == 0 and amount != 0:
            return {"received": False, "settled": False}
        else:
            return {"received": True, "settled": True}
        statuses = [
            {"received": True, "settled": True},
            {"received": False, "settled": False}
        ]
        return random.choice(statuses)
