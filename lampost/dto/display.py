from rootdto import RootDTO

class Display(RootDTO):
    def __init__(self, text=None, color=0x000000):
        self.display = RootDTO()
        self.display.lines = []
        if text is not None:
            self.append_line(DisplayLine(text, color))

    def merge(self, other):
        for line in other.display.lines:
            self.append_line(line)
        return self

    def append_line(self, line):
        self.display.lines.append(line)
        return self

    def append_text(self, text, color=0x000000):
        self.display.lines.append(DisplayLine(text, color))
        return self

    @property
    def feedback(self):
        return self

class DisplayLine(RootDTO):
    def __init__(self, text, color=0x000000):
        self.text = text
        self.color = color



