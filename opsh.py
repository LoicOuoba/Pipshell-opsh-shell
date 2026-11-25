import subprocess
import shlex
from opsh_builtins import ShellState, BUILTINS, expand_vars, try_assignment, expand_alias

def main():
    print("Bienvenue dans opsh !")
    st = ShellState()

    while True:
        try:
            # 1. Afficher le prompt et lire la commande
            line = input("opsh> ")

            # 2. Ignorer les lignes vides
            if not line.strip():
                continue

            # 3. Quitter le programme
            if line.strip() in ["exit", "quit"]:
                print("Au revoir !")
                break

            # 4. Découper la commande avec notre opérateur ->
            commands = line.split("->")

            # 5. Exécuter les commandes simples
            if len(commands) > 1:
                print("Les pipes seront implementes dans l'etape 3.")
                continue

            expanded = expand_vars(commands[0], st)
            args = shlex.split(expanded)

            if try_assignment(args, st):
                continue

            args = expand_alias(args, st)

            if args and args[0] in BUILTINS:
                st.last_status = BUILTINS[args[0]](args[1:], st)
                continue

            if args:
                try:
                    result = subprocess.run(args, env=st.env)
                    st.last_status = result.returncode
                except FileNotFoundError:
                    print(f"{args[0]}: command not found")
                    st.last_status = 127
        except KeyboardInterrupt:
            print()
        except EOFError:
            print("\nAu revoir !")
            break

if __name__ == "__main__":
    main()
