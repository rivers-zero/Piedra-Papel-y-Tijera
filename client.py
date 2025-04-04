# client.py
import secrets
from network import connect_to_server, send_data, receive_data
from game_logic import commit_move, verify_commit

# Replace 'SERVER_IP_ADDRESS' with the actual IP of the server machine obviously.
HOST = "SERVER_IP_ADDRESS"  
PORT = 5000

def main():
    print("Client: Connecting to server...")
    sock = connect_to_server(HOST, PORT)
    print("Client: Connected to server.")

    play = True
    while play:
        # --- Commit Phase ---
        # Receive server's commit
        server_commit_msg = receive_data(sock)
        if server_commit_msg is None or server_commit_msg.get("phase") != "commit":
            print("Error: Did not receive valid commit from server.")
            break
        server_commit = server_commit_msg.get("commit")
        print("Received server's commit.")
        
        # Prompt client user for move
        while True:
            move = input("Enter your move (rock, paper, scissors): ").strip().lower()
            if move in ["rock", "paper", "scissors"]:
                break
            else:
                print("Invalid move. Please try again.")
        
        nonce = secrets.token_hex(8)
        commit = commit_move(move, nonce)
        
        # Send client's commit
        commit_msg = {"phase": "commit", "commit": commit}
        send_data(sock, commit_msg)
        print("Commit sent.")
        
        # --- Reveal Phase ---
        # Receive server's reveal
        server_reveal_msg = receive_data(sock)
        if server_reveal_msg is None or server_reveal_msg.get("phase") != "reveal":
            print("Error: Did not receive valid reveal from server.")
            break
        server_move = server_reveal_msg.get("move")
        server_nonce = server_reveal_msg.get("nonce")
        print("Server has revealed their move.")
        
        # Send client's reveal (move and nonce)
        reveal_msg = {"phase": "reveal", "move": move, "nonce": nonce}
        send_data(sock, reveal_msg)
        print("Reveal sent.")
        
        # (Optional) Verify server's commit
        if not verify_commit(server_commit, server_move, server_nonce):
            print("Error: Server's commit does not match the reveal!")
        
        # --- Result Phase ---
        # Receive result from server
        result_msg = receive_data(sock)
        if result_msg is None or result_msg.get("phase") != "result":
            print("Error: Did not receive result from server.")
            break
        result = result_msg.get("result")
        print(f"Your move: {move}, Server move: {server_move}")
        print("Result:", result)
        
        # Wait for replay/exit decision from server
        decision_msg = receive_data(sock)
        if decision_msg is None:
            print("No decision received. Exiting.")
            break
        if decision_msg.get("phase") == "exit":
            print("Server decided to exit. Ending game.")
            play = False
        elif decision_msg.get("phase") == "replay":
            print("Starting a new round.")
        else:
            print("Unknown decision received. Exiting.")
            break

    print("Closing connection.")
    sock.close()

if __name__ == "__main__":
    main()
