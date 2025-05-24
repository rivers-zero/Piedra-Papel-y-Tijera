import tkinter as tk  # Standard GUI library for Python
from tkinter import messagebox, Toplevel, Label  # For dialogs and popup windows
import threading  # To run server socket in background thread
import secrets  # For generating secure random nonces
from network import setup_server_socket, accept_connection, send_data, receive_data  # Networking utilities
from game_logic import commit_move, verify_commit, determine_winner  # Game protocol and logic

# Network configuration for listening
HOST = "0.0.0.0"  # Listen on all available network interfaces
PORT = 5000       # Port to accept client connections on

# ASCII art for displaying moves
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

# Emoji labels for button text
EMOJIS = {"rock": "✊", "paper": "✋", "scissors": "✌"}

class RPSServerGUI:
    """
    GUI server for hosting a secure Rock-Paper-Scissors game
    Uses a commit-reveal protocol to ensure fair play
    """
    def __init__(self, root):
        """
        Initialize the server GUI:
        - Set up main window
        - Initialize state variables
        - Build widgets
        - Start server thread
        """
        self.root = root
        self.root.title("Rock Paper Scissors - Server")
        self.root.geometry("400x300")

        # Socket for listening and client connection
        self.server_sock = None
        self.conn = None        # Socket connection to client
        # Game state variables
        self.move = None        # Server's selected move
        self.nonce = None       # Random nonce for commit
        self.client_commit = None  # Commit hash received from client
        self.playing = True     # Flag to control game loop

        # Build UI and launch server
        self.create_widgets()
        threading.Thread(target=self.setup_server, daemon=True).start()

    def create_widgets(self):
        """
        Construct and arrange all GUI components:
        - Status label
        - Move buttons (disabled until ready)
        - Result label
        - Replay/Exit buttons
        """
        # Status message at top of window
        self.status_label = tk.Label(self.root, text="Starting server...", font=("Arial", 12))
        self.status_label.pack(pady=10)

        # Frame for move selection buttons
        self.button_frame = tk.Frame(self.root)
        self.buttons = {}
        for move in ["rock", "paper", "scissors"]:
            btn = tk.Button(
                self.button_frame,
                text=f"{EMOJIS[move]} {move.capitalize()}",
                font=("Arial", 14),
                command=lambda m=move: self.make_move(m),  # Bind selection handler
                state=tk.DISABLED  # Disabled until client connects
            )
            btn.pack(side=tk.LEFT, padx=10)
            self.buttons[move] = btn
        self.button_frame.pack(pady=20)

        # Label to display outcome text
        self.result_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.result_label.pack(pady=10)

        # Frame for replay/exit controls after round
        self.replay_frame = tk.Frame(self.root)
        # 'Play Again' button
        self.yes_button = tk.Button(
            self.replay_frame,
            text="Play Again",
            font=("Arial", 12),
            command=self.play_again,
            state=tk.DISABLED  # Enabled after round
        )
        # 'Exit' button
        self.no_button = tk.Button(
            self.replay_frame,
            text="Exit",
            font=("Arial", 12),
            command=self.quit_game,
            state=tk.DISABLED
        )
        self.yes_button.pack(side=tk.LEFT, padx=10)
        self.no_button.pack(side=tk.LEFT, padx=10)
        self.replay_frame.pack(pady=10)

    def setup_server(self):
        """
        Start listening for client connections.
        On connection, begin the game loop.
        """
        try:
            # Initialize listening socket
            self.server_sock = setup_server_socket(HOST, PORT)
            self.status_label.config(text="Waiting for client to connect...")
            # Block until a client connects
            self.conn, addr = accept_connection(self.server_sock)
            self.status_label.config(text=f"Client connected: {addr}")
            # Enter the main game loop
            self.run_game_loop()
        except Exception as e:
            # Show error dialog and update status
            messagebox.showerror("Server Error", str(e))
            self.status_label.config(text="Server error.")

    def run_game_loop(self):
        """
        Core server game loop:
        1. Let server choose a move
        2. Send server commit to client
        3. Receive client commit
        4. Reveal server move and nonce
        5. Receive client reveal and verify
        6. Determine winner and display result
        7. Handle replay/exit decision
        """
        while self.playing:
            # Prompt user to pick a move
            self.status_label.config(text="Choose your move.")
            self.enable_buttons()

            # Wait for button click
            while self.move is None:
                self.root.update_idletasks()
                self.root.update()

            # Create commit-reveal values
            self.nonce = secrets.token_hex(8)
            commit = commit_move(self.move, self.nonce)
            # Send commit phase to client
            send_data(self.conn, {"phase": "commit", "commit": commit})
            self.status_label.config(text="Commit sent. Waiting for client...")

            # Receive client commit and validate phase
            client_commit_msg = receive_data(self.conn)
            if not client_commit_msg or client_commit_msg.get("phase") != "commit":
                self.status_label.config(text="Error: Invalid commit from client.")
                return
            self.client_commit = client_commit_msg["commit"]

            # Reveal server move and nonce to client
            send_data(self.conn, {"phase": "reveal", "move": self.move, "nonce": self.nonce})
            self.status_label.config(text="Reveal sent. Waiting for client reveal...")

            # Receive client's reveal message
            client_reveal_msg = receive_data(self.conn)
            if not client_reveal_msg or client_reveal_msg.get("phase") != "reveal":
                self.status_label.config(text="Error: Invalid reveal from client.")
                return

            client_move = client_reveal_msg["move"]
            client_nonce = client_reveal_msg["nonce"]

            # Verify client's commit matches their reveal
            if not verify_commit(self.client_commit, client_move, client_nonce):
                # Commit mismatch indicates error or cheating
                result = "Client's commit did not match reveal!"
                winner = "invalid"
            else:
                # Determine winner of the round
                winner = determine_winner(self.move, client_move)
                if winner == "draw":
                    result = "It's a draw!"
                elif winner == "player1":
                    result = "You win!"
                else:
                    result = "Client wins!"

            # Update textual result display
            if result == "Client wins!":
                # From server perspective, client win means server lose
                self.result_label.config(
                    text=f"Your move: {self.move} | Client move: {client_move}\nResult: You lose!"
                )
            else:
                self.result_label.config(
                    text=f"Your move: {self.move} | Client move: {client_move}\nResult: {result}"
                )

            # Send result to client
            send_data(self.conn, {"phase": "result", "result": result})
            # Display ASCII art popup
            self.show_ascii_result(self.move, client_move, winner)

            # Enable replay/exit controls
            self.enable_replay_buttons()
            # Wait until user selects replay or exit
            while self.playing and self.move is not None:
                self.root.update_idletasks()
                self.root.update()

    def show_ascii_result(self, server_move, client_move, result):
        """
        Popup window showing ASCII art of both players' moves
        Colored to highlight the winner or draw state
        """
        result_window = tk.Toplevel(self.root)
        result_window.title("Round Result - Server")

        # Determine colors based on winner
        if result == "player2":
            client_color = "green"
            server_color = "red"
        elif result == "player1":
            client_color = "red"
            server_color = "green"
        else:
            client_color = server_color = "gold"

        # Create labels with ASCII art
        client_label = tk.Label(
            result_window,
            text=ASCII_ART[client_move],
            font=("Courier", 10),
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

        # Arrange ASCII labels in grid layout
        client_label.grid(row=0, column=0, padx=10, pady=10)
        vs_label.grid(row=0, column=1, padx=10, pady=10)
        server_label.grid(row=0, column=2, padx=10, pady=10)

    def make_move(self, move):
        """
        Handle move button click:
        - Record server's choice
        - Disable move buttons until round ends
        """
        self.move = move
        self.disable_buttons()

    def play_again(self):
        """
        Reset game state for another round:
        - Clear move and commit data
        - Reset labels and status
        - Disable replay controls until next end
        - Notify client to replay
        """
        self.move = None
        self.nonce = None
        self.client_commit = None
        self.result_label.config(text="")
        self.status_label.config(text="Starting new round...")
        self.disable_replay_buttons()
        send_data(self.conn, {"phase": "replay"})

    def quit_game(self):
        """
        Exit the game:
        - Set flag to stop loop
        - Inform client
        - Close sockets and GUI
        """
        self.playing = False
        send_data(self.conn, {"phase": "exit"})
        self.status_label.config(text="Game ended. Closing connection...")
        self.disable_replay_buttons()
        self.conn.close()
        self.server_sock.close()
        self.root.quit()

    def enable_buttons(self):
        """Enable move selection buttons"""
        for btn in self.buttons.values():
            btn.config(state=tk.NORMAL)

    def disable_buttons(self):
        """Disable move buttons to prevent input"""
        for btn in self.buttons.values():
            btn.config(state=tk.DISABLED)

    def enable_replay_buttons(self):
        """Enable 'Play Again' and 'Exit' buttons"""
        self.yes_button.config(state=tk.NORMAL)
        self.no_button.config(state=tk.NORMAL)

    def disable_replay_buttons(self):
        """Disable replay controls until appropriate"""
        self.yes_button.config(state=tk.DISABLED)
        self.no_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    # Entry point: launch server GUI
    root = tk.Tk()
    app = RPSServerGUI(root)
    root.mainloop()
