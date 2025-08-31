import streamlit as st
import json
from transaction import Transaction
from miner import Blockchain
import hashlib
import time

# Initialize session state
if 'blockchain' not in st.session_state:
    st.session_state.blockchain = Blockchain()
if 'accounts' not in st.session_state:
    st.session_state.accounts = {}
    st.session_state.accounts["Zakat_Account"] = {'balance': 0.0, 'roll_no': '0000'}
if 'pending_transactions' not in st.session_state:
    st.session_state.pending_transactions = []
if 'transaction_history' not in st.session_state:
    st.session_state.transaction_history = []

def calculate_zakat(amount):
    """Calculate zakat (2.5% of the amount)"""
    return amount * 0.025

def create_account(name, balance, roll_no):
    """Create a new account with initial balance and roll number"""
    if name in st.session_state.accounts:
        return False, "Account already exists"
    
    if balance < 0:
        return False, "Balance cannot be negative"
    
    if not roll_no or roll_no.strip() == "":
        return False, "Roll number cannot be empty"
    
    st.session_state.accounts[name] = {
        'balance': balance,
        'roll_no': roll_no.strip(),
        'created_at': time.time()
    }
    return True, f"Account '{name}' created with balance ${balance:.2f} and roll number {roll_no.strip()}"

def perform_transaction(sender, receiver, amount):
    """Perform a transaction between accounts with automatic zakat deduction"""
    if sender not in st.session_state.accounts:
        return False, f"Sender account '{sender}' does not exist. Please create it first."
    
    if receiver not in st.session_state.accounts:
        return False, f"Receiver account '{receiver}' does not exist. Please create it first."
    
    if amount <= 0:
        return False, "Amount must be positive"
    
    success, message = st.session_state.blockchain.validate_transaction_against_blockchain(sender, receiver, amount)
    if not success:
        return False, f"{message}"
    
    zakat_amount = calculate_zakat(amount)
    total_amount = amount + zakat_amount
    
    try:
        if "Zakat_Account" not in st.session_state.accounts:
            st.session_state.accounts["Zakat_Account"] = {'balance': 0.0, 'roll_no': '0000'}
        
        temp_accounts = {}
        for acc_name, acc_data in st.session_state.accounts.items():
            if isinstance(acc_data, dict):
                temp_accounts[acc_name] = acc_data['balance']
            else:
                temp_accounts[acc_name] = acc_data
        
        main_transaction = Transaction(sender, receiver, amount)
        main_transaction.apply(temp_accounts)
        
        zakat_transaction = Transaction(sender, "Zakat_Account", zakat_amount)
        zakat_transaction.apply(temp_accounts)
        
        for acc_name, balance in temp_accounts.items():
            if acc_name in st.session_state.accounts:
                if isinstance(st.session_state.accounts[acc_name], dict):
                    st.session_state.accounts[acc_name]['balance'] = balance
                else:
                    st.session_state.accounts[acc_name] = balance
        
        transaction_record = {
            'timestamp': time.time(),
            'sender': sender,
            'receiver': receiver,
            'amount': amount,
            'zakat_amount': zakat_amount,
            'total_cost': total_amount,
            'sender_remaining_balance': temp_accounts[sender],
            'type': 'transfer'
        }
        st.session_state.transaction_history.append(transaction_record)
        
        zakat_record = {
            'timestamp': time.time(),
            'sender': sender,
            'receiver': 'Zakat_Account',
            'amount': zakat_amount,
            'zakat_amount': 0,
            'total_cost': zakat_amount,
            'sender_remaining_balance': temp_accounts[sender],
            'type': 'zakat'
        }
        st.session_state.transaction_history.append(zakat_record)
        
        st.session_state.pending_transactions.extend([
            {
                'sender': sender,
                'receiver': receiver,
                'amount': amount,
                'type': 'transfer',
                'timestamp': time.time()
            },
            {
                'sender': sender,
                'receiver': 'Zakat_Account',
                'amount': zakat_amount,
                'type': 'zakat',
                'timestamp': time.time()
            }
        ])
        
        return True, f"Transaction successful! Transfer: ${amount:.2f}, Zakat: ${zakat_amount:.2f}"
    
    except Exception as e:
        return False, f"Transaction failed: {str(e)}"

def mine_block():
    """Mine a new block with pending transactions"""
    if not st.session_state.pending_transactions:
        return False, "No pending transactions to mine"
    
    first_tx = st.session_state.pending_transactions[0]
    sender = first_tx['sender']
    
    if sender in st.session_state.accounts:
        roll_no = st.session_state.accounts[sender]['roll_no']
    else:
        roll_no = "0000"
    
    success = st.session_state.blockchain.add_block(
        transactions=st.session_state.pending_transactions,
        roll_no=roll_no
    )
    
    if success:
        st.session_state.pending_transactions = []
        return True, f"Block mined successfully with roll number {roll_no}!"
    else:
        return False, "Failed to mine block"

def display_blockchain():
    """Display the blockchain in a readable format"""
    st.subheader("Blockchain")
    
    if len(st.session_state.blockchain.chain) == 1:
        st.info("Only genesis block exists. Mine some transactions to see more blocks!")
        return
    
    for i, block in enumerate(st.session_state.blockchain.chain):
        with st.expander(f"Block #{i} - {block.hash[:10]}..."):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Hash:** {block.hash}")
                st.write(f"**Previous Hash:** {block.prev_hash}")
                st.write(f"**Timestamp:** {time.ctime(block.timestamp)}")
                st.write(f"**Roll No (Seed Key):** {block.roll_no}")
            
            with col2:
                if i == 0:
                    st.write("**Content:** Genesis Block")
                else:
                    st.write("**Transactions:**")
                    for j, tx in enumerate(block.transactions):
                        tx_type = tx.get('type', 'transfer')
                        if tx_type == 'zakat':
                            st.write(f"  {j+1}. Zakat: {tx['sender']} → {tx['receiver']}: ${tx['amount']:.2f}")
                        else:
                            st.write(f"  {j+1}. Transfer: {tx['sender']} → {tx['receiver']}: ${tx['amount']:.2f}")

def display_accounts():
    """Display all accounts and their balances"""
    st.subheader("Account Balances")
    
    if not st.session_state.accounts:
        st.info("No accounts created yet.")
        return
    
    for account, account_data in st.session_state.accounts.items():
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            if account == "Zakat_Account":
                st.write(f"**{account}** (Special Account)")
            else:
                st.write(f"**{account}**")
        with col2:
            if isinstance(account_data, dict):
                st.write(f"${account_data['balance']:.2f}")
            else:
                st.write(f"${account_data:.2f}")
        with col3:
            if account != "Zakat_Account" and isinstance(account_data, dict):
                st.write(f"Roll: {account_data['roll_no']}")
            elif account == "Zakat_Account":
                st.write("N/A")
            else:
                st.write("Roll: 0000")

def display_transaction_history():
    """Display complete transaction history"""
    st.subheader("Transaction History")
    
    if not st.session_state.transaction_history:
        st.info("No transaction history available.")
        return
    
    for i, tx in enumerate(reversed(st.session_state.transaction_history)):
        with st.expander(f"Transaction #{len(st.session_state.transaction_history) - i}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Type:** {tx['type'].title()}")
                st.write(f"**Sender:** {tx['sender']}")
                st.write(f"**Receiver:** {tx['receiver']}")
                st.write(f"**Amount:** ${tx['amount']:.2f}")
            
            with col2:
                st.write(f"**Zakat:** ${tx['zakat_amount']:.2f}")
                st.write(f"**Total Cost:** ${tx['total_cost']:.2f}")
                st.write(f"**Remaining Balance:** ${tx['sender_remaining_balance']:.2f}")
                st.write(f"**Timestamp:** {time.ctime(tx['timestamp'])}")

def display_pending_transactions():
    """Display pending transactions waiting to be mined"""
    st.subheader("Pending Transactions")
    
    if not st.session_state.pending_transactions:
        st.info("No pending transactions.")
        return
    
    for i, tx in enumerate(st.session_state.pending_transactions):
        tx_type = tx.get('type', 'transfer')
        if tx_type == 'zakat':
            st.write(f"{i+1}. Zakat: {tx['sender']} → {tx['receiver']}: ${tx['amount']:.2f}")
        else:
            st.write(f"{i+1}. Transfer: {tx['sender']} → {tx['receiver']}: ${tx['amount']:.2f}")

# Streamlit UI
st.set_page_config(page_title="Zakat Blockchain Simulation", layout="wide")
st.title("Zakat Blockchain Simulation")
st.markdown("A blockchain system for simulating Zakat (2.5%) deduction and distribution with student nodes")

page = st.sidebar.selectbox(
    "Navigation",
    ["Dashboard", "Create Account", "Make Transaction", "Mine Block", "View Blockchain", "Transaction History", "Validate Chain"]
)

if page == "Dashboard":
    st.header("Dashboard")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Accounts", len(st.session_state.accounts))
    
    with col2:
        st.metric("Pending Transactions", len(st.session_state.pending_transactions))
    
    with col3:
        st.metric("Blocks in Chain", len(st.session_state.blockchain.chain))
    
    with col4:
        st.metric("Total Transactions", len(st.session_state.transaction_history))
    
    st.divider()
    
    col1, col2 = st.columns(2)
    
    with col1:
        display_accounts()
    
    with col2:
        display_pending_transactions()

elif page == "Create Account":
    st.header("Create New Account")
    
    if st.session_state.accounts:
        st.subheader("Existing Accounts")
        for account, account_data in st.session_state.accounts.items():
            if account == "Zakat_Account":
                if isinstance(account_data, dict):
                    st.write(f"• **{account}**: ${account_data['balance']:.2f} (Special Account)")
                else:
                    st.write(f"• **{account}**: ${account_data:.2f} (Special Account)")
            else:
                if isinstance(account_data, dict):
                    st.write(f"• **{account}**: ${account_data['balance']:.2f} (Roll: {account_data['roll_no']})")
                else:
                    st.write(f"• **{account}**: ${account_data:.2f} (Roll: 0000)")
        st.divider()
    
    with st.form("create_account_form"):
        account_name = st.text_input("Account Name", placeholder="e.g., Alice, Bob, Student_001")
        col1, col2 = st.columns(2)
        with col1:
            initial_balance = st.number_input("Initial Balance ($)", min_value=0.0, value=200.0, step=0.01)
        with col2:
            roll_no = st.text_input("Roll Number", placeholder="e.g., 2023001")
        
        if st.form_submit_button("Create Account"):
            if account_name.strip():
                success, message = create_account(account_name.strip(), initial_balance, roll_no)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Account name cannot be empty")
    
    st.info("**Tip**: Each student node starts with default 200 coins as per requirements!")

elif page == "Make Transaction":
    st.header("Make Transaction")
    
    if st.session_state.accounts:
        st.subheader("Available Accounts")
        for account, account_data in st.session_state.accounts.items():
            if account == "Zakat_Account":
                if isinstance(account_data, dict):
                    st.write(f"• **{account}**: ${account_data['balance']:.2f} (Special Account)")
                else:
                    st.write(f"• **{account}**: ${account_data:.2f} (Special Account)")
            else:
                if isinstance(account_data, dict):
                    st.write(f"• **{account}**: ${account_data['balance']:.2f} (Roll: {account_data['roll_no']})")
                else:
                    st.write(f"• **{account}**: ${account_data['balance']:.2f} (Roll: {account_data['roll_no']})")
        st.divider()
    
    if len(st.session_state.accounts) < 2:
        st.warning("You need at least 2 accounts to make transactions.")
        st.info("Go to 'Create Account' to add accounts first!")
        
        st.subheader("Quick Account Creation")
        with st.form("quick_account_form"):
            col1, col2, col3 = st.columns(3)
            with col1:
                quick_name = st.text_input("Account Name", placeholder="e.g., Alice")
            with col2:
                quick_balance = st.number_input("Initial Balance ($)", min_value=0.0, value=200.0, step=0.01)
            with col3:
                quick_roll_no = st.text_input("Roll Number", placeholder="e.g., 2023001")
            
            if st.form_submit_button("Create Account"):
                if quick_name.strip():
                    success, message = create_account(quick_name.strip(), quick_balance, quick_roll_no)
                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Account name cannot be empty")
    else:
        with st.form("transaction_form"):
            regular_accounts = [acc for acc in st.session_state.accounts.keys() if acc != "Zakat_Account"]
            sender = st.selectbox("Sender", regular_accounts)
            receiver = st.selectbox("Receiver", [acc for acc in regular_accounts if acc != sender])
            amount = st.number_input("Amount ($)", min_value=0.01, value=10.0, step=0.01)
            
            if sender in st.session_state.accounts:
                sender_data = st.session_state.accounts[sender]
                sender_balance = sender_data['balance']
                sender_roll = sender_data['roll_no']
                st.info(f"**{sender}**'s current balance: ${sender_balance:.2f} (Roll: {sender_roll})")
            
            zakat = calculate_zakat(amount)
            total_cost = amount + zakat
            st.info(f"Zakat (2.5%): ${zakat:.2f} | Total Cost: ${total_cost:.2f}")
            
            if sender in st.session_state.accounts:
                sender_data = st.session_state.accounts[sender]
                sender_balance = sender_data['balance']
                
                if sender_balance < total_cost:
                    st.error(f"Insufficient balance! {sender} needs ${total_cost:.2f} but has ${sender_balance:.2f}")
            
            if st.form_submit_button("Send Transaction"):
                success, message = perform_transaction(sender, receiver, amount)
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)

elif page == "Mine Block":
    st.header("Mine Block")
    
    if st.session_state.pending_transactions:
        st.info(f"Ready to mine {len(st.session_state.pending_transactions)} pending transactions")
        
        if st.button("Mine Block", type="primary"):
            with st.spinner("Mining block..."):
                success, message = mine_block()
                if success:
                    st.success(message)
                else:
                    st.error(message)
    else:
        st.info("No pending transactions to mine")
    
    display_pending_transactions()

elif page == "View Blockchain":
    st.header("Blockchain Explorer")
    display_blockchain()

elif page == "Transaction History":
    st.header("Transaction History")
    display_transaction_history()

elif page == "Validate Chain":
    st.header("Blockchain Validation")
    
    is_valid = st.session_state.blockchain.is_valid()
    
    if is_valid:
        st.success("Blockchain is valid!")
    else:
        st.error("Blockchain is invalid!")
    
    st.info(f"Chain length: {len(st.session_state.blockchain.chain)} blocks")
    
    if len(st.session_state.blockchain.chain) > 1:
        st.subheader("Validation Details")
        for i in range(1, len(st.session_state.blockchain.chain)):
            current = st.session_state.blockchain.chain[i]
            prev = st.session_state.blockchain.chain[i - 1]
            
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Block {i} Previous Hash:**")
                st.code(prev.hash)
            with col2:
                st.write(f"**Block {i} Stored Previous Hash:**")
                st.code(current.prev_hash)
            
            if current.prev_hash == prev.hash:
                st.success(f"Block {i} hash link is valid")
            else:
                st.error(f"Block {i} hash link is invalid")
            
            st.divider()

# Footer
st.sidebar.divider()
st.sidebar.markdown("---")
st.sidebar.markdown("**Features:**")
st.sidebar.markdown("• Student node accounts (200 coins default)")
st.sidebar.markdown("• Roll number-based hashing")
st.sidebar.markdown("• Automatic zakat (2.5%)")
st.sidebar.markdown("• Complete transaction history")
st.sidebar.markdown("• Block immutability verification")
