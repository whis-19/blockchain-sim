from block import Block

class Blockchain:
    """
    Blockchain class for Zakat Blockchain Simulation
    Manages the chain of blocks with roll number-based hashing and immutability verification
    """
    def __init__(self, roll_no="0000"):
        self.chain = []
        self.accounts = {}  # Track all accounts and their current balances
        # Initialize Zakat Account with proper structure
        self.accounts["Zakat_Account"] = {'balance': 0.0, 'roll_no': '0000'}
        self.create_genesis_block(roll_no)

    def create_genesis_block(self, roll_no):
        """
        Create the first block (genesis block)
        This is the foundation of the blockchain
        """
        genesis_block = Block(transactions="Genesis Block", prev_hash="0", roll_no=roll_no)
        self.chain.append(genesis_block)

    def add_block(self, transactions, roll_no):
        """
        Add a block to the chain after verifying previous hash
        Uses roll number as seed key for hashing to ensure uniqueness
        """
        if not self.chain:
            return False
        
        prev_block = self.chain[-1]
        new_block = Block(transactions=transactions, prev_hash=prev_block.hash, roll_no=roll_no)

        # Verify the new block's integrity before adding
        if new_block.verify_integrity() and new_block.prev_hash == prev_block.hash:
            self.chain.append(new_block)
            # Update account balances based on the new block's transactions
            self.update_account_balances_from_block(new_block)
            return True
        return False

    def update_account_balances_from_block(self, block):
        """
        Update account balances based on transactions in a block
        This maintains the current state of all accounts
        """
        if isinstance(block.transactions, list):
            for tx in block.transactions:
                if isinstance(tx, dict):
                    sender = tx.get('sender')
                    receiver = tx.get('receiver')
                    amount = tx.get('amount', 0)
                    
                    if sender and receiver and amount > 0:
                        # Initialize accounts if they don't exist
                        if sender not in self.accounts:
                            self.accounts[sender] = {'balance': 200.0, 'roll_no': '0000'}
                        if receiver not in self.accounts:
                            self.accounts[receiver] = {'balance': 200.0, 'roll_no': '0000'}
                        
                        # Handle different account data structures
                        if isinstance(self.accounts[sender], dict):
                            self.accounts[sender]['balance'] -= amount
                        else:
                            # Convert float to dict structure
                            self.accounts[sender] = {'balance': self.accounts[sender] - amount, 'roll_no': '0000'}
                        
                        if isinstance(self.accounts[receiver], dict):
                            self.accounts[receiver]['balance'] += amount
                        else:
                            # Convert float to dict structure
                            self.accounts[receiver] = {'balance': self.accounts[receiver] + amount, 'roll_no': '0000'}

    def get_all_accounts(self):
        """
        Get all accounts and their current balances from blockchain state
        """
        # Ensure all accounts are in the proper format
        formatted_accounts = {}
        for account_name, account_data in self.accounts.items():
            if isinstance(account_data, dict):
                formatted_accounts[account_name] = account_data
            else:
                # Convert float to dict structure
                formatted_accounts[account_name] = {'balance': account_data, 'roll_no': '0000'}
        return formatted_accounts

    def calculate_account_balance_from_history(self, account_name):
        """
        Calculate account balance from the entire blockchain history
        This is the authoritative way to determine current balance
        """
        balance = 0.0
        
        # Start with initial balance (200 coins for student accounts)
        if account_name != "Zakat_Account":
            balance = 200.0
        
        # Process all transactions in the blockchain
        for block in self.chain:
            if isinstance(block.transactions, list):
                for tx in block.transactions:
                    if isinstance(tx, dict):
                        if tx.get('sender') == account_name:
                            # Subtract the amount sent
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

    def validate_transaction_against_blockchain(self, sender, receiver, amount):
        """
        Validate a transaction against the entire blockchain state
        """
        # Calculate sender's current balance from blockchain history
        sender_balance = self.calculate_account_balance_from_history(sender)
        
        # Calculate zakat amount
        zakat_amount = amount * 0.025
        total_amount = amount + zakat_amount
        
        # Check if sender has sufficient balance
        if sender_balance < total_amount:
            return False, f"Insufficient balance. {sender} has ${sender_balance:.2f} but needs ${total_amount:.2f}"
        
        return True, "Transaction is valid"

    def is_valid(self):
        """
        Validate the entire blockchain by checking hashes and integrity
        Ensures immutability - any tampering will be detected
        """
        if len(self.chain) == 0:
            return False
        
        for i in range(len(self.chain)):
            current = self.chain[i]
            
            # Verify each block's integrity
            if not current.verify_integrity():
                return False
            
            # Check hash links (except for genesis block)
            if i > 0:
                prev = self.chain[i - 1]
                if current.prev_hash != prev.hash:
                    return False
        
        return True

    def get_latest_block(self):
        """
        Get the most recent block in the chain
        """
        if self.chain:
            return self.chain[-1]
        return None

    def get_block_by_index(self, index):
        """
        Get a specific block by its index in the chain
        """
        if 0 <= index < len(self.chain):
            return self.chain[index]
        return None

    def get_chain_length(self):
        """
        Get the total number of blocks in the chain
        """
        return len(self.chain)

    def get_transaction_history(self):
        """
        Get all transactions from all blocks in the chain
        """
        transactions = []
        for block in self.chain:
            if isinstance(block.transactions, list):
                transactions.extend(block.transactions)
        return transactions

    def verify_block_integrity(self, block_index):
        """
        Verify the integrity of a specific block
        """
        if 0 <= block_index < len(self.chain):
            return self.chain[block_index].verify_integrity()
        return False

    def get_roll_numbers_used(self):
        """
        Get all roll numbers used in the blockchain
        """
        roll_numbers = set()
        for block in self.chain:
            roll_numbers.add(block.roll_no)
        return list(roll_numbers)
