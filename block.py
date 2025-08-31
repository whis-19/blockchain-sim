import hashlib
import time
import json

class Block:
    """
    Block class for Zakat Blockchain Simulation
    Each block contains transactions, hash, previous hash, timestamp, and roll number seed key
    """
    def __init__(self, transactions, prev_hash, roll_no):
        self.transactions = transactions
        self.timestamp = time.time()
        self.roll_no = roll_no  # Student roll number as seed key
        self.prev_hash = prev_hash
        self.hash = self.compute_hash()   # Generate hash immediately

    def compute_hash(self):
        """
        Compute SHA-256 hash of block contents using roll number as seed key
        This ensures uniqueness and prevents hash collisions across multiple students
        """
        # Create a structured block data for hashing
        block_data = {
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'roll_no': self.roll_no,  # Seed key for uniqueness
            'prev_hash': self.prev_hash
        }
        
        # Convert to JSON string for consistent hashing
        block_string = json.dumps(block_data, sort_keys=True)
        
        # Use roll number as additional seed in hash computation
        # This ensures even similar blocks from different students have unique hashes
        seed_string = f"{block_string}_{self.roll_no}"
        
        return hashlib.sha256(seed_string.encode()).hexdigest()

    def to_dict(self):
        """
        Convert block to dictionary for serialization
        """
        return {
            'transactions': self.transactions,
            'timestamp': self.timestamp,
            'roll_no': self.roll_no,
            'prev_hash': self.prev_hash,
            'hash': self.hash
        }

    def verify_integrity(self):
        """
        Verify that the block's hash matches its computed hash
        This ensures immutability - any change to block data will invalidate the hash
        """
        computed_hash = self.compute_hash()
        return self.hash == computed_hash
