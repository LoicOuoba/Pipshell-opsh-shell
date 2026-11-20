import subprocess
import shlex

def main():
    print("Bienvenue dans opsh !")

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

            args = shlex.split(commands[0])

            if args:
                subprocess.run(args)

        except KeyboardInterrupt:
            print()
        except EOFError:
            print("\nAu revoir !")
            break

if __name__ == "__main__":
    main()
