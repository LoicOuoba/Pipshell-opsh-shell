import subprocess
import shlex


def execute_command(line):
    """Decouper et executer une commande ou un pipeline."""

    parts = line.split("->")

    commands = []

    for part in parts:
        part = part.strip()

        if not part:
            print("Erreur : commande vide dans le pipeline.")
            return

        try:
            args = shlex.split(part)
        except ValueError as error:
            print(f"Erreur de syntaxe : {error}")
            return

        if args:
            commands.append(args)

    if not commands:
        return

    # Execution d'une commande simple
    if len(commands) == 1:
        try:
            subprocess.run(commands[0], check=False)
        except FileNotFoundError:
            print(f"Commande introuvable : {commands[0][0]}")
        except OSError as error:
            print(f"Erreur d'execution : {error}")

        return

    # Execution d'un pipeline avec ->
    processes = []
    previous_process = None

    try:
        for i, args in enumerate(commands):

            if i == len(commands) - 1:
                process = subprocess.Popen(
                    args,
                    stdin=previous_process.stdout
                    if previous_process else None
                )
            else:
                process = subprocess.Popen(
                    args,
                    stdin=previous_process.stdout
                    if previous_process else None,
                    stdout=subprocess.PIPE
                )

            if previous_process:
                previous_process.stdout.close()

            previous_process = process
            processes.append(process)

        for process in processes:
            process.wait()

    except FileNotFoundError:
        print("Erreur : commande introuvable dans le pipeline.")

        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            process.wait()

    except OSError as error:
        print(f"Erreur d'execution du pipeline : {error}")


def main():
    """Boucle principale REPL."""

    print("Bienvenue dans OPSH !")

    while True:
        try:
            line = input("opsh> ")

            # Ignorer les lignes vides
            if not line.strip():
                continue

            # Quitter le mini-shell
            if line.strip() in ("exit", "quit"):
                print("Au revoir !")
                break

            # Executer la commande
            execute_command(line)

        except KeyboardInterrupt:
            print("\nInterruption : nouvelle commande.")

        except EOFError:
            print("\nAu revoir !")
            break


if __name__ == "__main__":
    main()
