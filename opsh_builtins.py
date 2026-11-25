import os
import re
import sys
import shlex

IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class ShellState:
    """Mémoire du shell : variables, alias, dernier code de retour."""
    def __init__(self):
        self.env = dict(os.environ)   # variables exportées
        self.vars = {}                # variables locales
        self.aliases = {
            "list": "ls", "show": "cat", "copy": "cp", "move": "mv",
            "del": "rm", "newdir": "mkdir", "newfile": "touch",
        }
        self.last_bg_pid = ""   # pour $!
        self.last_status = 0          # valeur de $?


# ---------- BUILTINS ----------
def b_pwd(args, st):
    print(os.getcwd())
    return 0


def b_echo(args, st):
    newline = True
    while args and re.fullmatch(r"-n+", args[0]):
        newline = False
        args = args[1:]
    print(" ".join(args), end="\n" if newline else "")
    return 0


def b_env(args, st):
    for k, v in st.env.items():
        print(f"{k}={v}")
    return 0


def b_cd(args, st):
    if len(args) > 1:
        print("cd: too many arguments", file=sys.stderr)
        return 1
    target = args[0] if args else st.env.get("HOME")
    if target == "-":
        target = st.env.get("OLDPWD")
        if not target:
            print("cd: OLDPWD not set", file=sys.stderr)
            return 1
        print(target)
    if not target:
        print("cd: HOME not set", file=sys.stderr)
        return 1
    old = os.getcwd()
    try:
        os.chdir(target)
    except OSError as e:
        print(f"cd: {target}: {e.strerror}", file=sys.stderr)
        return 1
    st.env["OLDPWD"] = old
    st.env["PWD"] = os.getcwd()
    return 0


def b_export(args, st):
    if not args:
        for k in sorted(st.env):
            print(f'declare -x {k}="{st.env[k]}"')
        return 0
    rc = 0
    for a in args:
        k, eq, v = a.partition("=")
        if not IDENT.match(k):
            print(f"export: `{a}': not a valid identifier", file=sys.stderr)
            rc = 1
        elif eq:
            st.env[k] = v
        elif k in st.vars:
            st.env[k] = st.vars.pop(k)
    return rc


def b_unset(args, st):
    rc = 0
    for k in args:
        if not IDENT.match(k):
            print(f"unset: `{k}': not a valid identifier", file=sys.stderr)
            rc = 1
        st.env.pop(k, None)
        st.vars.pop(k, None)
    return rc


def b_exit(args, st):
    if len(args) > 1:
        print("exit: too many arguments", file=sys.stderr)
        return 1
    code = st.last_status
    if args:
        try:
            code = int(args[0]) % 256
        except ValueError:
            print(f"exit: {args[0]}: numeric argument required", file=sys.stderr)
            code = 2
    print("Au revoir !")
    sys.exit(code)


def b_alias(args, st):
    if not args:
        for k, v in st.aliases.items():
            print(f"alias {k}='{v}'")
        return 0
    rc = 0
    for a in args:
        k, eq, v = a.partition("=")
        if eq:
            st.aliases[k] = v
        elif k in st.aliases:
            print(f"alias {k}='{st.aliases[k]}'")
        else:
            print(f"alias: {k}: not found", file=sys.stderr)
            rc = 1
    return rc


def b_unalias(args, st):
    if args == ["-a"]:
        st.aliases.clear()
        return 0
    rc = 0
    for k in args:
        if st.aliases.pop(k, None) is None:
            print(f"unalias: {k}: not found", file=sys.stderr)
            rc = 1
    return rc


def b_info(args, st):
    print("Commandes : go, path, say, export, unset, env, alias, unalias, info, osinfo, quit")
    print("Alias : list, show, copy, move, del, newdir, newfile")
    return 0


def b_osinfo(args, st):
    print("Systèmes d'Exploitation -- UIR/ESIN")
    return 0

BUILTINS = {
    "path": b_pwd, "say": b_echo, "env": b_env, "go": b_cd,
    "export": b_export, "unset": b_unset, "quit": b_exit,
    "alias": b_alias, "unalias": b_unalias,
    "info": b_info, "osinfo": b_osinfo,
}

# ---------- VARIABLES ----------
VAR = re.compile(r"\$(\?|\$|[A-Za-z_][A-Za-z0-9_]*|\{[A-Za-z_][A-Za-z0-9_]*\})")


def expand_vars(s, st):
    """Remplace $NOM, ${NOM}, $? et $$ (sauf entre quotes simples)."""
    out, i, quote = [], 0, None
    while i < len(s):
        c = s[i]
        if c in "'\"":
            if quote is None:
                quote = c
            elif quote == c:
                quote = None
        elif c == "$" and quote != "'":
            m = VAR.match(s, i)
            if m:
                name = m.group(1).strip("{}")
                if name == "?":
                    val = str(st.last_status)
                elif name == "$":
                    val = str(os.getpid())
                else:
                    val = st.vars.get(name, st.env.get(name, ""))
                out.append(val)
                i = m.end()
                continue
        out.append(c)
        i += 1
    return "".join(out)


def try_assignment(tokens, st):
    """Gère NOM=valeur. Renvoie True si c'était une assignation."""
    if len(tokens) == 1 and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[0]):
        k, _, v = tokens[0].partition("=")
        if k in st.env:
            st.env[k] = v
        else:
            st.vars[k] = v
        return True
    return False


# ---------- ALIAS ----------
def expand_alias(tokens, st):
    """Remplace le 1er mot s'il est un alias (sans boucle infinie)."""
    seen = set()
    while tokens and tokens[0] in st.aliases and tokens[0] not in seen:
        seen.add(tokens[0])
        tokens = shlex.split(st.aliases[tokens[0]]) + tokens[1:]
    return tokens

