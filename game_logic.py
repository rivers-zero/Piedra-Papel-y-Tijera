# game_logic.py
import hashlib

def commit_move(move, nonce):
    """
    Generate a commit hash for the move using the nonce.
    Returns a hexadecimal string (SHA256 hash of move+nonce).
    """
    return hashlib.sha256((move + nonce).encode()).hexdigest()

def verify_commit(commit, move, nonce):
    """
    Verify that the commit matches the hash of the move concatenated with the nonce.
    Returns True if valid, otherwise False.
    """
    return commit == commit_move(move, nonce)

def determine_winner(move1, move2):
    """
    Determine the winner between two moves.
    Returns:
      - "draw" if both moves are the same.
      - "player1" if move1 wins over move2.
      - "player2" if move2 wins over move1.
    """
    if move1 == move2:
        return "draw"
    if move1 == "rock":
        return "player1" if move2 == "scissors" else "player2"
    if move1 == "paper":
        return "player1" if move2 == "rock" else "player2"
    if move1 == "scissors":
        return "player1" if move2 == "paper" else "player2"
