
"""
substitution.py
Partie 4 du projet OPSH
Substitution de commandes, .opshrc,
historique et complétion.
"""

import os
import re
import readline
import subprocess
from pathlib import Path


class ShellFeatures:

    def __init__(self, execute_line=None):
        self.execute_line = execute_line
        self.history_file = Path.home() / ".opsh_history"
        self.rc_file = Path.home() / ".opshrc"

    # 1. Substitution des commandes $(...) et `...`

    def run_subcommand(self, command):

        if self.execute_line is not None:
            try:
                result = self.execute_line(command, capture=True)
                if result is not None:
                    return str(result).rstrip("\n")
            except TypeError:
                pass

        result = subprocess.run(
            command,
            shell=True,
            text=True,
            capture_output=True
        )

        return result.stdout.rstrip("\n")

    def substitute(self, text):

        # Remplacer $(commande)
        pattern = r"\$\((.*?)\)"

        def replace(match):
            command = match.group(1)
            return self.run_subcommand(command)

        text = re.sub(pattern, replace, text)

        # Remplacer `commande`
        pattern = r"`([^`]*)`"

        def replace_backticks(match):
            command = match.group(1)
            return self.run_subcommand(command)

        text = re.sub(pattern, replace_backticks, text)

        return text

    # 2. Expansion des variables

    def expand_variables(self, text, last_status=0,
                         last_background_pid=""):

        def replace(match):

            name = match.group(1) or match.group(2)

            if name == "?":
                return str(last_status)

            if name == "!":
                return str(last_background_pid)

            return os.environ.get(name, "")

        pattern = (
            r"\$\{([A-Za-z_][A-Za-z0-9_]*|\?|\!)\}"
            r"|\$([A-Za-z_][A-Za-z0-9_]*|\?|\!)"
        )

        return re.sub(pattern, replace, text)

    def expand(self, text, last_status=0,
               last_background_pid=""):

        text = self.substitute(text)

        text = self.expand_variables(
            text,
            last_status,
            last_background_pid
        )

        return text

    # 3. Chargement du fichier .opshrc

    def load_opshrc(self):

        if not self.rc_file.exists():
            return

        with open(self.rc_file, "r", encoding="utf-8") as file:

            for line in file:

                command = line.strip()

                if command and not command.startswith("#"):

                    if self.execute_line:
                        self.execute_line(command)

    # 4. Historique des commandes

    def load_history(self):

        try:
            readline.read_history_file(
                str(self.history_file)
            )

        except FileNotFoundError:
            pass

        readline.set_history_length(1000)

    def add_history(self, command):

        if command.strip():
            readline.add_history(command)

    def save_history(self):

        try:
            readline.write_history_file(
                str(self.history_file)
            )

        except OSError as error:
            print("Erreur historique :", error)

    def show_history(self):

        for i in range(
            1,
            readline.get_current_history_length() + 1
        ):

            command = readline.get_history_item(i)

            print(f"{i}  {command}")

    # 5. Complétion automatique avec TAB

    def setup_completion(self, commands=None):

        commands = commands or [
            "go", "quit", "path", "say",
            "info", "past", "osinfo",
            "list", "show", "copy",
            "move", "del", "newdir",
            "newfile"
        ]

        def complete(text, state):

            options = [
                command for command in commands
                if command.startswith(text)
            ]

            # Complétion des fichiers
            if "/" in text or text.startswith("."):

                options = [
                    file for file in os.listdir(".")
                    if file.startswith(text)
                ]

            if state < len(options):
                return options[state]

            return None

        readline.set_completer(complete)

        readline.parse_and_bind("tab: complete")

    # Initialisation et fermeture

    def startup(self):

        self.load_history()

        self.setup_completion()

        self.load_opshrc()

    def shutdown(self):

        self.save_history()
