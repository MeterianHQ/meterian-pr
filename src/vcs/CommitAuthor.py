class CommitAuthor:

    def __init__(self, username, email) -> None:
        self.username = username
        self.email = email

    def getUsername(self):
        return self.username

    def getEmail(self):
        return self.email

    def __str__(self) -> str:
        return "CommitAuthor [ username=" + self.username + ", email=" + self.email + " ]"