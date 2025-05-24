# Piedra-Papel-y-Tijera
Classic game of piedra, papel y tijera over a TCP socket connection with TKinter GUI.

# Rock‑Paper‑Scissors Secure GUI

A client‑server Rock‑Paper‑Scissors game implemented in Python using Tkinter for the GUI and a commit‑reveal protocol for fair play. The server and client communicate over TCP sockets, ensuring neither side can cheat by committing to a move with a secure hash before revealing it.

---

## Features

* **Commit‑Reveal Protocol**: Prevents cheating by exchanging hashed commits before revealing moves.
* **GUI Interfaces**: Separate Tkinter windows for client and server with move buttons, status updates, and ASCII‑art results.
* **Network Module**: Simple JSON‑over‑TCP communication layer (`network.py`).
* **Game Logic Module**: SHA‑256 hashing for commits, commit verification, and winner determination (`game_logic.py`).
* **ASCII Art**: Fun text visuals for rock, paper, and scissors.
* **Replay & Exit**: After each round, choose to play again or exit cleanly.

---

## Prerequisites

* Python 3.7+
* Standard library modules (no external dependencies):

  * `tkinter` (GUI)
  * `socket`, `json`, `hashlib`, `threading`, `secrets`

## Project Structure

```
├── README.md
├── client.py              # Client GUI application
├── server.py              # Server GUI application
├── game_logic.py          # Commit‑reveal and winner logic
└── network.py             # TCP networking utilities
```

## Installation & Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd <repository-directory>
   ```

2. **Ensure Python 3 is installed**

   ```bash
   python3 --version
   ```

3. **(Optional) Create and activate a virtual environment**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   venv\\Scripts\\activate  # Windows
   ```

## Usage

### 1. Run the Server

In one terminal, start the server GUI:

```bash
python3 server.py
```

* The server listens on all interfaces (`0.0.0.0`) at port `5000` by default.
* The window will show “Starting server...” then “Waiting for client to connect….”

### 2. Run the Client

In another terminal (same machine or different), start the client GUI:

```bash
python3 client.py
```

* By default, the client connects to `127.0.0.1:5000`.
* The window will show “Connecting to server…” then “Connected to server. Waiting for commit…”

### 3. Play

1. Once connected, the server chooses a move first and sends a commit.
2. The client is prompted to pick rock, paper, or scissors.
3. Both sides exchange reveals (move + nonce) and verify commits.
4. The result is displayed in a popup with ASCII art and colored text.
5. Choose **Play Again** or **Exit** on the server window to continue or end the game.

## File Descriptions

* **`game_logic.py`**

  * `commit_move(move, nonce)`: Returns SHA-256 hash of `move + nonce`.
  * `verify_commit(commit, move, nonce)`: Checks if `commit` matches the hash.
  * `determine_winner(move1, move2)`: Returns "draw", "player1", or "player2".

* **`network.py`**

  * `setup_server_socket(host, port)`: Creates and listens on a TCP socket.
  * `accept_connection(server_sock)`: Blocks until a client connects.
  * `connect_to_server(host, port)`: Connects a client socket.
  * `send_data(sock, data)`: Sends a JSON message over the socket.
  * `receive_data(sock)`: Receives and parses a JSON message.

* **`server.py`**

  * Hosts the game: GUI for server move selection, commit/reveal exchange, and replay logic.
  * Runs the server socket and game loop in a background thread.

* **`client.py`**

  * Client interface: connects to server, handles commit/reveal, and displays results.
  * Keeps the GUI responsive by running network operations in a separate thread.

## Customization

* **Port & Host**: Modify the `HOST` and `PORT` constants at the top of each GUI script.
* **Timeouts & Error Handling**: Currently minimal; consider adding socket timeouts or retries.
* **Styling**: Change fonts, window size, or ASCII art in the scripts to personalize.

## License

This project is released under the MIT License. Feel free to use and modify!

---

*Have fun and fair play!*
