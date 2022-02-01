from __future__ import annotations

from rich.console import Console

from texas import TexasHoldem, PlayerInfo, actions
from typing import Literal

console = Console()


def main():  # noqa: C901
    game = TexasHoldem(max=2, stakes=(15, 30))
    stack = 3000
    game.generate_players(stack=stack)
    game.new_game()
    rnd = game.brm.round

    human = game.tm.players[0]
    bot = game.tm.players[1]

    console.rule()
    console.print(f"sb/bb: {game.stakes}, you stack: {stack}, bot stack: {stack}")

    ti = game.table_info
    console.rule(f"[bold]Hand: {game.tm.epoch}")
    console.print(f'Board: {ti["board"]}, Pot: {sum(p.value for p in ti["pots"])}, Round: {ti["round"]}')

    while True:
        info = game.current_player_info
        # プレイヤーのアクション
        if game.current_player.id == human.id:
            p = game.current_player
            console.print(f"Position: {p.position}, Hole: {p.hole}, Stack: {p.stack}")
            action = player_action(info)
            game.execute(action)
            console.print()
        # botのアクション
        else:
            action = bot_action(info)
            game.execute(action)
            console.print()

        # Roundの変化を検知
        if rnd != game.brm.round:
            rnd = game.brm.round
            info = game.table_info
            console.print(f'Board: {info["board"]}, Pot: {sum(p.value for p in info["pots"])}, Round: {info["round"]}')

        # 精算 & Next game
        if game.is_completion:
            h_refund, b_refund = game.last_refunds[human.position], game.last_refunds[bot.position]
            console.print(f"You: {human.hole}, Bot: {bot.hole}")
            console.print(f"You: {human.stack}(+{h_refund}), Bot: {bot.stack}(+{b_refund})")
            game.next_game()
            if bot.stack < 2 * game.stakes[1] or human.stack < 2 * game.stakes[1]:
                txt = "You win!" if bot.stack < human.stack else "You lose"
                console.rule("[bold cyan]" + txt)
                break
            console.rule(f"[bold]Hand: {game.tm.epoch}")
            info = game.table_info
            console.print(f'Board: {info["board"]}, Pot: {sum(p.value for p in info["pots"])}, Round: {info["round"]}')


def player_action(info: PlayerInfo) -> actions:  # noqa: C901
    action = None
    while True:
        action = console.input(f'Select action {info["playable_actions"]}: ').upper()
        action = omit(action, info["playable_actions"])
        if action in info["playable_actions"]:
            break
    value = 0
    if action in ("RAISE", "BET"):
        rr = info.get("bet_range") or (0, 0)
        while not (rr[0] <= value <= rr[1]):
            txt = console.input(f'Bet amount? {info.get("bet_range")}: ')
            try:
                value = int(txt)
            except ValueError:
                continue
    # pylanceがエラー出さないようにはこう書くしかなかった...
    if action == "RAISE":
        return {"type": action, "value": value}
    if action == "BET":
        return {"type": action, "value": value}
    if action == "CALL":
        return {"type": action}
    if action == "CHECK":
        return {"type": action}
    return {"type": action}


def bot_action(info: PlayerInfo) -> actions:
    if "CALL" in info["playable_actions"]:
        call_value = info.get("call_value") or 0
        all_in = "[red](ALL-IN)[/ red]" if call_value >= info["stack"] else ""
        console.print(f"[cyan]BotはCALLしました[/ cyan]{all_in}, value: {call_value}, stack: {info['stack']}")
        return {"type": "CALL"}
    else:
        console.print(f"[cyan]BotはCHECKしました, , stack: {info['stack']}")
        return {"type": "CHECK"}


def omit(txt: str, actions: list[str]):
    c = "CALL" if "CALL" in actions else "CHECK"
    dic: dict[str, Literal["FOLD", "CHECK", "BET", "CALL", "RAISE"]] = {
        "C": c,
        "B": "BET",
        "R": "RAISE",
        "F": "FOLD",
    }
    dic.update({"CALL": c, "CHECK": "CHECK", "BET": "BET", "RAISE": "RAISE", "FOLD": "FOLD"})
    return dic.get(txt)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n終了")
