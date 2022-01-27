import logging

class BranchHelper:
    
    PR_BRANCH_NAME_PREFIX = "meterian-bot/autofix/"

    log = logging.getLogger("BranchHelper")

    def to_branch_ref(self, branch_name: str) -> str:
        ref = self.__sanitize_github_ref(branch_name)
        if ref == "refs/heads/" or ref == "refs/heads/@":
            self.log.warn("Invalid ref %s was generated", ref)
            return None
        else:
            return "refs/heads/" + ref

    def as_branch_name(self, ref: str) -> str:
        return ref.replace("refs/heads/", "")
    
    def as_branch_ref(self, branch_name: str) -> str:
        return "refs/heads/" + branch_name

    def __replace_if(self, old: str, new: str, condition: bool) -> str:
        if condition:
            return new
        else:
            return old

    def __remove_control_chars(self, text):
        new_text = ""
        for charr in text:
            new_text+=self.__replace_if(charr, "", ord(charr) <= 32 or ord(charr) == 127)
        return new_text

    def __sanitize_github_ref(self, name: str) -> str:
        if name == "refs/heads/" or name == "refs/heads/@":
            return name

        new_name = ""
        tokens = name.split("/")
        for token in tokens:
            token = self.__replace_if(token, token[1:], token.startswith("."))
            token = self.__replace_if(token, token[0:len(token)-1], token.endswith("."))
            token = self.__replace_if(token, token.replace(".lock", "_lock"), token.endswith(".lock"))
            token = token.replace("..", "_")
            token = token.replace("~", "_")
            token = token.replace("^", "_")
            token = token.replace(":", "_")
            token = token.replace("?", "_")
            token = token.replace("*", "_")
            token = token.replace("[", "_")
            token = token.replace("@{", "_")
            token = token.replace("\\", "_")
            token = self.__remove_control_chars(token)

            if new_name == "":
                new_name = token
            else:
                new_name = self.__replace_if(new_name, "/".join([new_name, token]), token != "")
        return new_name