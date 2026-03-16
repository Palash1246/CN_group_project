import threading

# Shared leaderboard dictionary
leaderboard = {}

# Lock to prevent race conditions
lock = threading.Lock()


def update_score(player, score):
    """
    Safely update the score of a player.

    If player exists -> add score
    If player doesn't exist -> create entry
    """

    # Only one thread can execute this block at a time
    with lock:

        if player in leaderboard:
            leaderboard[player] += score
        else:
            leaderboard[player] = score

        return leaderboard[player]


def get_leaderboard():
    """
    Return a sorted leaderboard.
    Highest score first.
    """

    with lock:

        # Sort players by score
        sorted_board = sorted(
            leaderboard.items(),
            key=lambda x: x[1],
            reverse=True
        )

        return sorted_board


def reset_leaderboard():
    """
    Clears all scores (useful for testing)
    """

    with lock:
        leaderboard.clear()
