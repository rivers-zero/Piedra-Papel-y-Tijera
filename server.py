import tkinter as tk
from tkinter import messagebox, Toplevel, Label
import threading
import secrets
from network import setup_server_socket, accept_connection, send_data, receive_data
from game_logic import commit_move, verify_commit, determine_winner

HOST = "0.0.0.0"
PORT = 5000


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

EMOJIS = {
    "rock": "✊", "paper": "✋", "scissors": "✌"
}

class RPSServerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock Paper Scissors - Server")
        self.root.geometry("400x300") 

        self.server_sock = None
        self.conn = None
        self.move = None
        self.nonce = None
        self.client_commit = None
        self.playing = True

        self.create_widgets()
        threading.Thread(target=self.setup_server, daemon=True).start()

    def create_widgets(self):
        self.status_label = tk.Label(self.root, text="Starting server...", font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.button_frame = tk.Frame(self.root)
        self.buttons = {}
        for move in ["rock", "paper", "scissors"]:
            btn = tk.Button(
                self.button_frame,
                text=f"{EMOJIS[move]} {move.capitalize()}",
                font=("Arial", 14),
                command=lambda m=move: self.make_move(m),
                state=tk.DISABLED
            )
            btn.pack(side=tk.LEFT, padx=10)
            self.buttons[move] = btn
        self.button_frame.pack(pady=20)

        self.result_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.result_label.pack(pady=10)

        self.replay_frame = tk.Frame(self.root)
        self.yes_button = tk.Button(self.replay_frame, text="Play Again", font=("Arial", 12),
                                    command=self.play_again, state=tk.DISABLED)
        self.no_button = tk.Button(self.replay_frame, text="Exit", font=("Arial", 12),
                                   command=self.quit_game, state=tk.DISABLED)
        self.yes_button.pack(side=tk.LEFT, padx=10)
        self.no_button.pack(side=tk.LEFT, padx=10)
        self.replay_frame.pack(pady=10)

        
        

    def setup_server(self):
        try:
            self.server_sock = setup_server_socket(HOST, PORT)
            self.status_label.config(text="Waiting for client to connect...")
            self.conn, addr = accept_connection(self.server_sock)
            self.status_label.config(text=f"Client connected: {addr}")
            self.run_game_loop()
        except Exception as e:
            messagebox.showerror("Server Error", str(e))
            self.status_label.config(text="Server error.")

    def run_game_loop(self):
        while self.playing:
            self.status_label.config(text="Choose your move.")
            self.enable_buttons()

            while self.move is None:
                self.root.update_idletasks()
                self.root.update()

            self.nonce = secrets.token_hex(8)
            commit = commit_move(self.move, self.nonce)
            send_data(self.conn, {"phase": "commit", "commit": commit})
            self.status_label.config(text="Commit sent. Waiting for client...")

            client_commit_msg = receive_data(self.conn)
            if not client_commit_msg or client_commit_msg.get("phase") != "commit":
                self.status_label.config(text="Error: Invalid commit from client.")
                return
            self.client_commit = client_commit_msg["commit"]

            send_data(self.conn, {"phase": "reveal", "move": self.move, "nonce": self.nonce})
            self.status_label.config(text="Reveal sent. Waiting for client reveal...")

            client_reveal_msg = receive_data(self.conn)
            if not client_reveal_msg or client_reveal_msg.get("phase") != "reveal":
                self.status_label.config(text="Error: Invalid reveal from client.")
                return

            client_move = client_reveal_msg["move"]
            client_nonce = client_reveal_msg["nonce"]

            if not verify_commit(self.client_commit, client_move, client_nonce):
                result = "Client's commit did not match reveal!"
                winner = "invalid"
            else:
                winner = determine_winner(self.move, client_move)
                if winner == "draw":
                    result = "It's a draw!"
                elif winner == "player1":
                    result = "You win!"
                else:
                    result = "Client wins!"

            if result == "Client wins!":
                self.result_label.config(
                    text=f"Your move: {self.move} | Client move: {client_move}\nResult: You lose!"
                )
            elif result == "You win!":
                self.result_label.config(
                    text=f"Your move: {self.move} | Client move: {client_move}\nResult: {result}"
                )
            elif result == "It's a draw!":
                self.result_label.config(
                    text=f"Your move: {self.move} | Client move: {client_move}\nResult: {result}"
                )
            else:
                self.result_label.config(
                    text=f"Your move: {self.move} | Client move: {client_move}\nResult: {result}"
                )       

            send_data(self.conn, {"phase": "result", "result": result})
            self.show_ascii_result(self.move, client_move, winner)

            self.enable_replay_buttons()
            while self.playing and self.move is not None:
                self.root.update_idletasks()
                self.root.update()

    def show_ascii_result(self, server_move, client_move, result):
        result_window = tk.Toplevel(self.root)
        result_window.title("Round Result - Server")

        if result == "player2":
            client_color = "green"
            server_color = "red"
        elif result == "player1":
            client_color = "red"
            server_color = "green"
        else:
            client_color = server_color = "gold"

        client_label = tk.Label(result_window, text=ASCII_ART[client_move], font=("Courier", 10), fg=client_color, justify=tk.LEFT)
        vs_label = tk.Label(result_window, text="VS", font=("Arial", 12))
        server_label = tk.Label(result_window, text=ASCII_ART[server_move], font=("Courier", 10), fg=server_color, justify=tk.LEFT)

        client_label.grid(row=0, column=0, padx=10, pady=10)
        vs_label.grid(row=0, column=1, padx=10, pady=10)
        server_label.grid(row=0, column=2, padx=10, pady=10)

    def make_move(self, move):
        self.move = move
        self.disable_buttons()

    def play_again(self):
        self.move = None
        self.nonce = None
        self.client_commit = None
        self.result_label.config(text="")
        self.status_label.config(text="Starting new round...")
        self.disable_replay_buttons()
        send_data(self.conn, {"phase": "replay"})

    def quit_game(self):
        self.playing = False
        send_data(self.conn, {"phase": "exit"})
        self.status_label.config(text="Game ended. Closing connection...")
        self.disable_replay_buttons()
        self.conn.close()
        self.server_sock.close()
        self.root.quit()

    def enable_buttons(self):
        for btn in self.buttons.values():
            btn.config(state=tk.NORMAL)

    def disable_buttons(self):
        for btn in self.buttons.values():
            btn.config(state=tk.DISABLED)

    def enable_replay_buttons(self):
        self.yes_button.config(state=tk.NORMAL)
        self.no_button.config(state=tk.NORMAL)

    def disable_replay_buttons(self):
        self.yes_button.config(state=tk.DISABLED)
        self.no_button.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = RPSServerGUI(root)
    root.mainloop()
