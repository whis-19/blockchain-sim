import time

class Transaction:
    """
    Transaction class for Zakat Blockchain Simulation
    Handles financial transactions with proper validation against blockchain state
    """
    def __init__(self, sender, receiver, amount):
        self.sender = sender
        self.receiver = receiver
        self.amount = amount
        self.timestamp = time.time()

    def validate_against_blockchain(self, blockchain, accounts):
        """
        Validate transaction against the entire blockchain state
        This ensures the sender has sufficient balance based on all previous transactions
        """
        # Calculate current balance from blockchain history
        sender_balance = self.calculate_balance_from_blockchain(blockchain, self.sender)
        
        # Check if sender has sufficient balance
        if sender_balance < self.amount:
            return False, f"Insufficient balance. {self.sender} has ${sender_balance:.2f} but needs ${self.amount:.2f}"
        
        # Check if both accounts exist
        if self.sender not in accounts:
            return False, f"Sender account '{self.sender}' does not exist."
        
        if self.receiver not in accounts:
            return False, f"Receiver account '{self.receiver}' does not exist."
        
        # Validate amount is positive
        if self.amount <= 0:
            return False, "Transaction amount must be positive."
        
        # Check for self-transaction
        if self.sender == self.receiver:
            return False, "Sender and receiver cannot be the same"
        
        return True, "Transaction is valid"

    def calculate_balance_from_blockchain(self, blockchain, account_name):
        """
        Calculate account balance from the entire blockchain history
        This simulates how real blockchains validate transactions
        """
        balance = 0.0
        
        # Start with initial balance if account exists in current accounts
        # For student accounts, this would be 200 coins
        if account_name in blockchain.get_all_accounts():
            balance = blockchain.get_all_accounts()[account_name].get('balance', 0.0)
        
        # Process all transactions in the blockchain to calculate current balance
        for block in blockchain.chain:
            if isinstance(block.transactions, list):
                for tx in block.transactions:
                    if isinstance(tx, dict):
                        # Handle transaction from blockchain
                        if tx.get('sender') == account_name:
                            # Subtract the amount sent (including zakat)
                            if tx.get('type') == 'transfer':
                                balance -= tx.get('amount', 0)
                                # Also subtract zakat amount
                                zakat_amount = tx.get('amount', 0) * 0.025
                                balance -= zakat_amount
                            elif tx.get('type') == 'zakat':
                                balance -= tx.get('amount', 0)
                        
                        if tx.get('receiver') == account_name:
                            # Add the amount received
                            balance += tx.get('amount', 0)
        
        return balance

    def apply(self, accounts):
        """
        Apply the transaction to the accounts dictionary.
        This method is used for immediate balance updates after validation
        """
        # Validate that both sender and receiver exist
        if self.sender not in accounts:
            raise Exception(f"Sender account '{self.sender}' does not exist.")
        
        if self.receiver not in accounts:
            raise Exception(f"Receiver account '{self.receiver}' does not exist.")

        # Validate amount is positive
        if self.amount <= 0:
            raise Exception("Transaction amount must be positive.")

        # Check if sender has sufficient balance
        if accounts[self.sender] < self.amount:
            raise Exception(f"Insufficient balance. {self.sender} has ${accounts[self.sender]:.2f} but needs ${self.amount:.2f}")

        # Perform the transaction
        accounts[self.sender] -= self.amount
        accounts[self.receiver] += self.amount

        return accounts

    def to_dict(self):
        """
        Convert transaction to dictionary for serialization
        """
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': self.timestamp
        }

    def validate(self):
        """
        Validate transaction data
        """
        if not self.sender or not self.receiver:
            return False, "Sender and receiver cannot be empty"
        
        if self.sender == self.receiver:
            return False, "Sender and receiver cannot be the same"
        
        if self.amount <= 0:
            return False, "Amount must be positive"
        
        return True, "Transaction is valid"

    def get_transaction_summary(self):
        """
        Get a summary of the transaction
        """
        return {
            'sender': self.sender,
            'receiver': self.receiver,
            'amount': self.amount,
            'timestamp': time.ctime(self.timestamp),
            'type': 'transfer'
        }
