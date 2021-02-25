"""
This is a script that lets you and your friends share a world without paying for a dedicated server.
The script makes sure that only one is hosting at a time.

Setup steps:

1. Put this file (asa_words.py) in a new folder
2. Copy your current world (from ~/AppData/LocalLow/IronGate/Valheim/worlds) into a folder with the same name as the world
    e.g. If your world's name is "MyWorld", the structure should look like this:

    MyNewlyCreatedFolder/
    ├── MyWorld/
    │   ├── MyWorld.db
    │   ├── MyWorld.db.old
    │   ├── MyWorld.fwl
    │   └── MyWorld.fwl.old
    └── asa_worlds.py

3. Create a git-repo in "MyNewlyCreatedFolder" ( git init )
4. Create an empty GitHub-repo (no README, no nothing)
5. Add the GitHub-repo as a remote the repo in "MyNewlyCreatedFolder"
    ( git remote add origin https://github.com/<username>/<reponame>.git )
6. Add push this folder to the GitHub repo
    ( git add . )
    ( git commit -m "Initial commit" )
    ( git branch -M main )
    ( git push -u origin/main )
7. Start asa_worlds.py and let it run before starting Valheim ( python3 asa_worlds.py )
8. Exit asa_worlds.py after exiting Valheim by pressing Ctrl+C
9. Done! Invite your friends to clone the repo. OBS! They only have to do steps 6 and 7.


P.S: SSH Authentication for GitHub is strongly recommended, as failed 
      authentication isn't handled at all here.
P.S.S: Change `WORLD_NAME` if your world name isn't "MyWorld".
"""

import shutil
import subprocess as sp
import sys
import time
from datetime import datetime
from pathlib import Path

try:
  from termcolor import colored
except ImportError:
  def colored(string, *args, **kwargs):
    return string

WORLD_NAME = "MyWorld"
HERE = Path(".")
GITTED_FOLDER = HERE / WORLD_NAME
TIME_STAMP = datetime.now().strftime("%d%m%Y-%H%M%S")

WORLDS_FOLDER = Path.home() / "AppData" / "LocalLow" / "IronGate" / "Valheim" / "worlds"


def mayor_print(string):
    print(colored("="*80, "blue", attrs=["bold"]))
    print(" " * 19, colored(string, attrs=["bold"]))
    print(colored("="*80, "blue", attrs=["bold"]))


def minor_print(string):
    print(colored("-" * 19, "blue", attrs=["bold"]), string)


def shell_command(split_cmd, cwd=HERE):
    """ Runs a shell command and returns False if the return code is non-zero """
    print(colored(f'Kör "{" ".join(split_cmd)}"', 'blue', attrs=['bold']))
    try:
        sp.run(split_cmd, cwd=cwd, check=True)
        return True
    except sp.CalledProcessError:
        return False


def copy_files(file_paths, new_dir):
    assert len(list(file_paths)) == 4
    print("Försöker kopiera 4 filer från:")
    print("    ", file_paths[0].parent)
    print("till:")
    print("    ", new_dir)

    for file_path in file_paths:
        destination = new_dir / file_path.name
        shutil.copy(file_path.absolute(), destination.absolute())


def move_files(file_paths, new_dir):
    assert len(list(file_paths)) == 4
    print("Försöker flytta 4 filer från:")
    print("    ", file_paths[0].parent)
    print("till:")
    print("    ", new_dir)

    for file_path in file_paths:
        destination = new_dir / file_path.name
        file_path.absolute().rename(destination.absolute())


def backup_old_world():
    minor_print(f"Skapar backup för {WORLD_NAME}")

    backup_folder = WORLDS_FOLDER / ("backup_" + WORLD_NAME + "_" + TIME_STAMP)
    present_world_files = list(WORLDS_FOLDER.glob(WORLD_NAME + "*"))

    if len(present_world_files) == 4:
        backup_folder.mkdir()
        move_files(present_world_files, backup_folder)
    elif len(present_world_files) == 0:
        print(f'Hittade inga filer för "{WORLD_NAME}" i\n\t{WORLDS_FOLDER}')
        print("Antingen är den redan back-uppad eller så finns inga filer.")
    else:
        print("WTH, dude. SOmething is wrong in your files")
        print(f'hittade bara {len(present_world_files)} saker som heter "{WORLD_NAME}"')


def move_gitted_world_to_appdata():
    minor_print("Flyttar världsfiler från lokala repot till AppData ...")

    gitted_files = list(GITTED_FOLDER.glob(WORLD_NAME + "*"))

    if len(gitted_files) == 4:
        copy_files(gitted_files, WORLDS_FOLDER)
        return True
    else:
        print(f'Satan! Inga världsfiler i repot för "{WORLD_NAME}"')
        print(f'Se till att flytta de filer du har i\n\t{WORLDS_FOLDER}')
        print(f'Till mappen "{GITTED_FOLDER}"')
        return False


def commit_world():
    minor_print("Commitar världen ...")

    world_files_paths = list(WORLDS_FOLDER.glob(WORLD_NAME + "*"))
    copy_files(world_files_paths, GITTED_FOLDER)

    world_files_to_add = list(GITTED_FOLDER.glob(WORLD_NAME + "*"))
    world_files_to_add = map(Path.as_posix, world_files_to_add)
    shell_command(["git", "add", *world_files_to_add])
    shell_command(["git", "commit", "-m", f"Update world {WORLD_NAME}"])


def git_pull():
    minor_print("Pullar ...")
    assert shell_command(["git", "pull"])


def git_push():
    minor_print("Pushar till origin/main ...")
    assert shell_command(["git", "push", "-u", "origin", "main"])


def try_aquire_lock():
    """ Returns true if the lock is aquired, false otherwise """
    minor_print("Försöker skaffa låset ...")

    lock_path = GITTED_FOLDER / "lock"

    try:
        lock_path.touch()
    except FileExistsError:
        return False

    shell_command(["git", "add", lock_path.as_posix()])
    shell_command(["git", "commit", "-m", f"Aquired lock for {WORLD_NAME}"])
    return True


def release_lock():
    minor_print("Släpper låset ...")
    lock_path = GITTED_FOLDER / "lock"
    shell_command(["git", "rm", lock_path.as_posix()])
    shell_command(["git", "commit", "-m", f"Released lock for {WORLD_NAME}"])


def main():
    mayor_print("Uppdaterar")
    git_pull()

    mayor_print("Försöker starta")
    if not try_aquire_lock():
        print("Någon använder redan världen!")
        sys.exit(0)

    mayor_print("Bytar plats på repo-världen och det som finns i AppData ...")
    backup_old_world()
    if not move_gitted_world_to_appdata():
        print("Kunde inte flytta världen till AppData :(")
        print("Din förra värld är i en ny mapp. Vill du komma åt den så får du fixa't själv.")
        sys.exit(1)

    mayor_print("Start klar!")
    print("Nu kan du köra igång Valheim!")
    print()
    print('Tryck "Ctrl+C" när du stängt ner servern och vill pusha världen.')

    try:
        # Wait for Ctrl-C.
        while True:
            time.sleep(1000)
    except KeyboardInterrupt:
        commit_world()
        release_lock()
        git_push()
        mayor_print("Tack haaaj!")


def check_shell_program_deps(deps):
    """
    Returns true if all deps exists on the system.
    Testing if return code from "program --version" is 0.
    """
    for dep in deps:
        success = shell_command([dep, "--version"])
        if not success:
            print(dep, "är nog inte installerat :(")
            return False
    print("Alla skal-kommandon finns!")
    return True

if __name__ == "__main__":
    mayor_print("Kollar miljön")

    # kolla om vi är på windows
    if sys.platform != "win32":
        print("Du verkar inte köra på Windows! Se till att göra det!")
        sys.exit(0)

    # kolla om scriptet körs från rätt mapp
    if Path(__file__).parent.absolute() != Path.cwd().absolute():
        print("Fan, sorry. Men du måste vara i denna mappen:")
        print("   ", Path(__file__).parent.absolute())
        sys.exit(1)

    # kollar om grejjor är installerade.
    if not check_shell_program_deps(["git"]):
        sys.exit(1)

    # kollar om världen finns i repot.
    if not GITTED_FOLDER.exists():
        print(f'"{GITTED_FOLDER}" verkar inte finnas i repot. Avslutar...')
        sys.exit(1)

    main()
