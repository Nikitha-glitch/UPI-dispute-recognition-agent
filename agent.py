from mock_api import MockBankAPI, MockMerchantAPI
from models import db, Transaction, Dispute

class UPIDisputeAgent:
    def __init__(self, transaction_id):
        self.transaction_id = transaction_id
        self.bank_api = MockBankAPI()
        self.merchant_api = MockMerchantAPI()

    def verify_and_resolve(self):
        txn = Transaction.query.get(self.transaction_id)
        if not txn:
            return {"error": "Transaction not found."}

        # If it's already resolved/success, maybe skip
        if txn.status == 'SUCCESS':
            return {
                "transaction_status": "SUCCESS",
                "dispute_status": "Transaction Successful. Money credited to receiver.",
                "merchant_txn_id": f"MERCH-{self.transaction_id}",
                "receiver_txn_id": f"BANK-{self.transaction_id}",
                "bank_info": {"debited": True, "credited": True},
                "merchant_info": {"received": True, "settled": True}
            }

        # 1. Check Bank Status (Pass transaction amount for test flags)
        bank_info = self.bank_api.get_transaction_status(self.transaction_id, txn.amount)
        
        # 2. Check Merchant Status (Pass transaction amount for test flags)
        merchant_txn_id = f"MERCH-{self.transaction_id}"
        merchant_info = self.merchant_api.get_merchant_transaction_status(merchant_txn_id, txn.amount)

        dispute_status = "Investigation Pending"
        final_txn_status = txn.status
        receiver_txn_id = f"BANK-{self.transaction_id}"

        # Core Dispute Agent Logic
        if bank_info['debited'] and merchant_info['received']:
            final_txn_status = 'SUCCESS'
            dispute_status = 'Transaction Successful. Merchant Received Funds.'
            
        elif txn.amount % 2 == 0 and txn.amount != 0:
            # Multiples of 2: Dispute Resolved (No Debit)
            final_txn_status = 'DISPUTE_RESOLVED'
            dispute_status = 'Dispute Resolved. Money is not credited nor debited from account.'

        elif txn.amount % 5 == 0 and txn.amount != 0:
            # Multiples of 5 (odd: 5, 15...): Refund Initiated
            if bank_info['debited']:
                # Money debited but not received by merchant
                self.bank_api.initiate_refund(self.transaction_id, txn.amount)
                final_txn_status = 'REFUND_INITIATED'
                dispute_status = 'Refund Initiated. Money debited from your account.'
                
                # Refund money back to user mock balance
                if txn.user and txn.status != 'REFUND_INITIATED': 
                    txn.user.balance += txn.amount
            else:
                final_txn_status = 'REFUND_INITIATED'
                dispute_status = 'Refund Initiated. Money debited from your account.'

        elif bank_info['debited'] and not merchant_info['received']:
            # Fallback for non-multiples of 5 if such a case exists
            refund_resp = self.bank_api.initiate_refund(self.transaction_id, txn.amount)
            final_txn_status = 'REFUND_CREDITED'
            dispute_status = f"Refund Credited. Reference: {refund_resp['refund_id']}"
            if txn.user and txn.status != 'REFUND_CREDITED':
                txn.user.balance += txn.amount
            
        elif not bank_info['debited'] and not merchant_info['received']:
            # Money wasn't debited and merchant didn't receive it
            final_txn_status = 'FAILED'
            dispute_status = 'Dispute Resolved. Money was not debited.'
            
        else:
            final_txn_status = 'MANUAL_REVIEW'
            dispute_status = 'Dispute requires manual review.'

        txn.status = final_txn_status
        
        # Log into Dispute History
        dispute = Dispute(
            transaction_id=self.transaction_id,
            merchant_txn_id=merchant_txn_id,
            receiver_txn_id=receiver_txn_id,
            dispute_status=dispute_status
        )
        db.session.add(dispute)
        db.session.commit()

        return {
            "transaction_status": final_txn_status,
            "dispute_status": dispute_status,
            "merchant_txn_id": merchant_txn_id,
            "receiver_txn_id": receiver_txn_id,
            "bank_info": bank_info,
            "merchant_info": merchant_info
        }
