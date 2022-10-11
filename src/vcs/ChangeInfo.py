class ChangeInfo:
    def __init__(self, file_path, content) -> None:
        self.file_path = file_path
        self.content = content

    def __str__(self) -> str:
        return "ChangeInfo [ file_path=" + self.file_path + ", content=" + self.content + " ]"