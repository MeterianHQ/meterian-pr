class LabelData:

    def __init__(self, name, description, color, text_color) -> None:
        self.name = name
        self.description = description
        self.color = color
        self.text_color = text_color

    def to_payload(self) -> dict:
        return self.__dict__

    def __str__(self) -> str:
        return "LabelData [ name=" +str(self.name) + ", description=" +str(self.description) + ", color=" +str(self.color) + ", text_color=" +str(self.text_color) + " ]"

if __name__ == "__main__":
    label = LabelData("test", "label description", "#gggggg", "#ffffff")
    print(label.to_payload())