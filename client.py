import tkinter as tk  # Standard GUI library for Python
from tkinter import messagebox  # For popup dialogs (error/info)
import secrets  # For generating secure random nonces
import threading  # To run network connection in background thread
from network import connect_to_server, send_data, receive_data  # Custom module for network communication
from game_logic import commit_move, verify_commit  # Custom module for commit-reveal game logic

# Server connection parameters
HOST = "127.0.0.1"
PORT = 5000

# ASCII art representations for the three moves
ASCII_ART = {
    "rock": """
    _______
---'   ____)    
      (_____)
      (_____)
      (____)
---.__(___)
""",
    "paper": """
     _______
---'    ____)____
           ______)
          _______)
         _______)
---.__________)
""",
    "scissors": """
    _______
---'   ____)____
          ______)
       __________)
      (____)
---.__(___)
"""
}

class RPSClientGUI:
    """
    GUI client for playing a secure Rock-Paper-Scissors game
    Implements a commit-reveal protocol to prevent cheating
    """
    def __init__(self, root):
        """
        Initialize the application:
        - Set up the main window
        - Initialize network and game state variables
        - Create GUI widgets
        - Start background thread to connect to server
        """
        self.root = root
        self.root.title("Rock Paper Scissors - Client")
        self.sock = None          # Socket connection to server
        self.move = None          # Client's selected move
        self.nonce = None         # Random nonce for commit-reveal
        self.server_commit = None # Commit value received from server
        self.root.geometry("400x300")  # Set window size

        self.create_widgets()
        # Launch connection in a separate thread to avoid blocking the GUI
        threading.Thread(target=self.connect_to_server, daemon=True).start()

    def create_widgets(self):
        """
        Build and layout all GUI components:
        - Status label for connection and game prompts
        - Buttons for rock/paper/scissors (initially disabled)
        - Label to display round results
        """
        # Status text at top
        self.status_label = tk.Label(self.root, text="Connecting to server...", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Frame to hold move buttons
        self.button_frame = tk.Frame(self.root)
        self.buttons = {}
        # Emoji labels for each move
        emojis = {"rock": "✊", "paper": "✋", "scissors": "✌"}
        for move in ["rock", "paper", "scissors"]:
            # Create a button for each move
            btn = tk.Button(
                self.button_frame,
                text=f"{emojis[move]} {move.capitalize()}",
                font=("Arial", 14),
                command=lambda m=move: self.make_move(m),  # Bind to make_move handler
                state=tk.DISABLED  # Disabled until ready to choose
            )
            btn.pack(side=tk.LEFT, padx=10)
            self.buttons[move] = btn
        self.button_frame.pack(pady=20)

        # Label to show textual result summary
        self.result_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.result_label.pack(pady=10)

        # Ensure consistent geometry (repeated call)
        self.root.geometry("400x300")  

    def connect_to_server(self):
        """
        Attempt to establish connection to the game server.
        On success, update status and start the game loop.
        On failure, show error message.
        """
        try:
            self.sock = connect_to_server(HOST, PORT)
            # Update status to indicate successful connection
            self.status_label.config(text="Connected to server. Waiting for commit...")
            self.play_game()
        except Exception as e:
            # Connection failed: update status and alert user
            self.status_label.config(text="Connection failed.")
            messagebox.showerror("Connection Error", str(e))

    def play_game(self):
        """
        Main game loop:
        1. Wait for server's commit
        2. Let client choose move
        3. Send client's commit
        4. Receive server's reveal and verify its commit
        5. Send client's reveal
        6. Receive and display result
        7. Handle replay or exit
        """
        while True:
            # Prompt waiting for commit from server
            self.status_label.config(text="Waiting for server's commit...")
            server_commit_msg = receive_data(self.sock)
            # Validate incoming message phase
            if not server_commit_msg or server_commit_msg.get("phase") != "commit":
                self.status_label.config(text="Error: Invalid commit from server.")
                return

            # Store the server's commit hash
            self.server_commit = server_commit_msg["commit"]
            # Prompt user to choose move
            self.status_label.config(text="Choose your move.")
            self.enable_buttons()

            # Wait until user clicks a button and self.move is set
            while self.move is None:
                self.root.update_idletasks()
                self.root.update()

            # Create a secure random nonce for the commit
            self.nonce = secrets.token_hex(8)
            # Generate client's commit hash
            client_commit = commit_move(self.move, self.nonce)
            # Send commit message to server
            send_data(self.sock, {"phase": "commit", "commit": client_commit})
            self.status_label.config(text="Commit sent. Waiting for server reveal...")

            # Receive server's reveal message
            server_reveal_msg = receive_data(self.sock)
            if not server_reveal_msg or server_reveal_msg.get("phase") != "reveal":
                self.status_label.config(text="Error: Invalid reveal from server.")
                return

            # Extract server's revealed move and nonce
            server_move = server_reveal_msg["move"]
            server_nonce = server_reveal_msg["nonce"]

            # Send client's reveal (move + nonce)
            send_data(self.sock, {"phase": "reveal", "move": self.move, "nonce": self.nonce})
            self.status_label.config(text="Reveal sent. Waiting for result...")

            # Verify server's commit matches the revealed values
            if not verify_commit(self.server_commit, server_move, server_nonce):
                # Mismatch indicates tampering or error
                self.result_label.config(text="Server's reveal did not match commit!", fg="red")
            else:
                # Receive and process result message
                result_msg = receive_data(self.sock)
                if not result_msg or result_msg.get("phase") != "result":
                    self.status_label.config(text="Error: No result received.")
                    return

                result = result_msg["result"]
                # Display ASCII art and text based on result
                self.show_ascii_result(self.move, server_move, result)
                # Update textual result label for client perspective
                if result == "You win!":
                    # Note: server's perspective is inverted
                    self.result_label.config(
                        text=f"Your move: {self.move} | Server move: {server_move}\nResult: You lose!"
                    )
                elif result == "Client wins!":
                    self.result_label.config(
                        text=f"Your move: {self.move} | Server move: {server_move}\nResult: You win!"
                    )
                elif result == "It's a draw!":
                    self.result_label.config(
                        text=f"Your move: {self.move} | Server move: {server_move}\nResult: {result}"
                    )
                else:
                    # Catch-all for unexpected result strings
                    self.result_label.config(
                        text=f"Your move: {self.move} | Server move: {server_move}\nResult: {result}"
                    )

            # After displaying round, wait for server's decision to replay or exit
            decision_msg = receive_data(self.sock)
            if not decision_msg:
                self.status_label.config(text="No decision from server. Exiting.")
                return
            elif decision_msg["phase"] == "exit":
                self.status_label.config(text="Server exited the game.")
                return
            elif decision_msg["phase"] == "replay":
                # Reset state for next round
                self.move = None
                self.nonce = None
                self.server_commit = None
                self.status_label.config(text="New round starting...")
                self.result_label.config(text="")
            else:
                # Unrecognized phase: abort
                self.status_label.config(text="Unknown server decision. Exiting.")
                return

    def show_ascii_result(self, client_move, server_move, result):
        """
        Open a new window to display ASCII art of both players' moves,
        colored to highlight winner/loser or draw.
        """
        result_window = tk.Toplevel(self.root)
        result_window.title("Round Result - Client")

        # Determine text colors based on outcome
        if result == "Client wins!":
            client_color = "green"
            server_color = "red"
        elif result == "You win!":
            # From client's perspective, this means client lost
            client_color = "red"
            server_color = "green"
        else:
            client_color = server_color = "gold"  # Draw

        # Create labels for ASCII art
        client_label = tk.Label(
            result_window,
            text=ASCII_ART[client_move],
            font=("Courier", 10),  # Monospace for ASCII art alignment
            fg=client_color,
            justify=tk.LEFT
        )
        vs_label = tk.Label(result_window, text="VS", font=("Arial", 12))
        server_label = tk.Label(
            result_window,
            text=ASCII_ART[server_move],
            font=("Courier", 10),
            fg=server_color,
            justify=tk.LEFT
        )

        # Arrange the three labels in a grid
        client_label.grid(row=0, column=0, padx=10, pady=10)
        vs_label.grid(row=0, column=1, padx=10, pady=10)
        server_label.grid(row=0, column=2, padx=10, pady=10)

    def make_move(self, selected_move):
        """
        Callback for when a move button is clicked:
        - Store the selected move
        - Disable the buttons to prevent multiple clicks
        """
        self.move = selected_move
        self.disable_buttons()

    def enable_buttons(self):
        """
        Enable all move buttons so the user can make a choice.
        """
        for btn in self.buttons.values():
            btn.config(state=tk.NORMAL)

    def disable_buttons(self):
        """
        Disable all move buttons to prevent further input until reset.
        """
        for btn in self.buttons.values():
            btn.config(state=tk.DISABLED)


if __name__ == "__main__":
    # Entry point: create main window and run the GUI event loop
    root = tk.Tk()
    app = RPSClientGUI(root)
    root.mainloop()
