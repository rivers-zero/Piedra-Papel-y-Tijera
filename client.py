import tkinter as tk
from tkinter import messagebox
import secrets
import threading
from network import connect_to_server, send_data, receive_data
from game_logic import commit_move, verify_commit

HOST = "127.0.0.1"
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

class RPSClientGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Rock Paper Scissors - Client")
        self.sock = None
        self.move = None
        self.nonce = None
        self.server_commit = None
        self.root.geometry("400x300")  

        self.create_widgets()
        threading.Thread(target=self.connect_to_server, daemon=True).start()

    def create_widgets(self):
        self.status_label = tk.Label(self.root, text="Connecting to server...", font=("Arial", 12))
        self.status_label.pack(pady=10)

        self.button_frame = tk.Frame(self.root)
        self.buttons = {}
        emojis = {"rock": "✊", "paper": "✋", "scissors": "✌"}
        for move in ["rock", "paper", "scissors"]:
            btn = tk.Button(
                self.button_frame,
                text=f"{emojis[move]} {move.capitalize()}",
                font=("Arial", 14),
                command=lambda m=move: self.make_move(m),
                state=tk.DISABLED
            )
            btn.pack(side=tk.LEFT, padx=10)
            self.buttons[move] = btn
        self.button_frame.pack(pady=20)

        self.result_label = tk.Label(self.root, text="", font=("Arial", 14))
        self.result_label.pack(pady=10)

        self.root.geometry("400x300")  


    def connect_to_server(self):
        try:
            self.sock = connect_to_server(HOST, PORT)
            self.status_label.config(text="Connected to server. Waiting for commit...")
            self.play_game()
        except Exception as e:
            self.status_label.config(text="Connection failed.")
            messagebox.showerror("Connection Error", str(e))

    def play_game(self):
        while True:
            self.status_label.config(text="Waiting for server's commit...")
            server_commit_msg = receive_data(self.sock)
            if not server_commit_msg or server_commit_msg.get("phase") != "commit":
                self.status_label.config(text="Error: Invalid commit from server.")
                return

            self.server_commit = server_commit_msg["commit"]
            self.status_label.config(text="Choose your move.")
            self.enable_buttons()

            while self.move is None:
                self.root.update_idletasks()
                self.root.update()

            self.nonce = secrets.token_hex(8)
            client_commit = commit_move(self.move, self.nonce)
            send_data(self.sock, {"phase": "commit", "commit": client_commit})
            self.status_label.config(text="Commit sent. Waiting for server reveal...")

            server_reveal_msg = receive_data(self.sock)
            if not server_reveal_msg or server_reveal_msg.get("phase") != "reveal":
                self.status_label.config(text="Error: Invalid reveal from server.")
                return

            server_move = server_reveal_msg["move"]
            server_nonce = server_reveal_msg["nonce"]

            send_data(self.sock, {"phase": "reveal", "move": self.move, "nonce": self.nonce})
            self.status_label.config(text="Reveal sent. Waiting for result...")

            if not verify_commit(self.server_commit, server_move, server_nonce):
                self.result_label.config(text="Server's reveal did not match commit!", fg="red")
            else:
                result_msg = receive_data(self.sock)
                if not result_msg or result_msg.get("phase") != "result":
                    self.status_label.config(text="Error: No result received.")
                    return

                result = result_msg["result"]
                self.show_ascii_result(self.move, server_move, result)
                if result == "You win!":
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
                    self.result_label.config(
                        text=f"Your move: {self.move} | Server move: {server_move}\nResult: {result}"
                    )



            decision_msg = receive_data(self.sock)
            if not decision_msg:
                self.status_label.config(text="No decision from server. Exiting.")
                return
            elif decision_msg["phase"] == "exit":
                self.status_label.config(text="Server exited the game.")
                return
            elif decision_msg["phase"] == "replay":
                self.move = None
                self.nonce = None
                self.server_commit = None
                self.status_label.config(text="New round starting...")
                self.result_label.config(text="")
            else:
                self.status_label.config(text="Unknown server decision. Exiting.")
                return

    def show_ascii_result(self, client_move, server_move, result):
        result_window = tk.Toplevel(self.root)
        result_window.title("Round Result - Client")

        if result == "Client wins!":
            client_color = "green"
            server_color = "red"
        elif result == "You win!":
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

    def make_move(self, selected_move):
        self.move = selected_move
        self.disable_buttons()

    def enable_buttons(self):
        for btn in self.buttons.values():
            btn.config(state=tk.NORMAL)

    def disable_buttons(self):
        for btn in self.buttons.values():
            btn.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    app = RPSClientGUI(root)
    root.mainloop()
