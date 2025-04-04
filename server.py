# server.py
import secrets
from network import setup_server_socket, accept_connection, send_data, receive_data
from game_logic import commit_move, verify_commit, determine_winner

HOST = "0.0.0.0"  # Listen on all network interfaces
PORT = 5000       # Choose an available port

def main():
    print("Server: Setting up server...")
    server_sock = setup_server_socket(HOST, PORT)
    print("Server: Waiting for client connection...")
    conn, addr = accept_connection(server_sock)
    print(f"Server: Connected by {addr}")

    play_again = True
    while play_again:
        # --- Commit Phase ---
        # Prompt server user for move
        while True:
            move = input("Enter your move (rock, paper, scissors): ").strip().lower()
            if move in ["rock", "paper", "scissors"]:
                break
            else:
                print("Invalid move. Please try again.")
        
        nonce = secrets.token_hex(8)
        commit = commit_move(move, nonce)
        
        # Send commit to client
        commit_msg = {"phase": "commit", "commit": commit}
        send_data(conn, commit_msg)
        print("Commit sent. Waiting for client's commit...")
        
        # Receive client's commit
        client_commit_msg = receive_data(conn)
        if client_commit_msg is None or client_commit_msg.get("phase") != "commit":
            print("Error: Did not receive valid commit from client.")
            break
        client_commit = client_commit_msg.get("commit")
        print("Received client's commit.")
        
        # --- Reveal Phase ---
        # Send server's reveal (move and nonce)
        reveal_msg = {"phase": "reveal", "move": move, "nonce": nonce}
        send_data(conn, reveal_msg)
        print("Reveal sent. Waiting for client's reveal...")
        
        # Receive client's reveal
        client_reveal_msg = receive_data(conn)
        if client_reveal_msg is None or client_reveal_msg.get("phase") != "reveal":
            print("Error: Did not receive valid reveal from client.")
            break
        client_move = client_reveal_msg.get("move")
        client_nonce = client_reveal_msg.get("nonce")
        
        # Verify client's commit
        if not verify_commit(client_commit, client_move, client_nonce):
            print("Error: Client's commit does not match the reveal!")
            result = "Invalid move from client."
        else:
            # Determine the winner
            winner = determine_winner(move, client_move)
            if winner == "draw":
                result = "It's a draw!"
            elif winner == "player1":
                result = "You win!"
            elif winner == "player2":
                result = "Client wins!"
        
        print(f"Server move: {move}, Client move: {client_move}")
        print("Result:", result)
        
        # Send result message to client
        result_msg = {"phase": "result", "result": result}
        send_data(conn, result_msg)
        
        # Ask server user if they want to play again
        replay = input("Play again? (y/n): ").strip().lower()
        if replay != "y":
            play_again = False
            send_data(conn, {"phase": "exit"})
        else:
            send_data(conn, {"phase": "replay"})
    
    print("Closing connection.")
    conn.close()
    server_sock.close()

if __name__ == "__main__":
    main()
