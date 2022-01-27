import os
import subprocess
import logging
import traceback

class GitCli:

    __log = logging.getLogger("GitCli")
    __git_ls_command = [ "git", "ls-files", "-m" ]

    def __init__(self, dir):
        self.dir = dir

    def get_changes(self) -> list:
        envvars = os.environ.copy()

        try:
            process = subprocess.Popen(
                self.__git_ls_command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.dir,
                env=envvars
            )

            stdout, stderr = self.__process(process)
            exit_code = process.poll()
            if exit_code != 0:
                self.__log.error("Command %s failed\n%s", self.__git_ls_command, stderr)
            else:
                self.__log.debug("Changes detected were \n%s", stdout)
                if stdout != "":
                    return stdout.split("\n")
                else:
                    return []
        except:
            self.__log.error("Unexpected exception caught while attempting to get changes from git", exc_info=1)

        return None 

    def __process(self, process: subprocess.Popen):
        stdout, stderr = process.communicate()
        out = stdout.decode("utf-8").strip()
        err = stderr.decode("utf-8")
        return out, err

if __name__ == "__main__":
    git = GitCli("/home/nana/meterian/isaac/")
    changes = git.get_changes()
    print(changes)

    print("Trying to get absolute path of first change")
    print("From this %s to" % changes[0])
    absolute_path = os.path.abspath(changes[0])
    print(absolute_path)
    print("absolute path of the absolute path?")
    print(os.path.abspath(absolute_path))
