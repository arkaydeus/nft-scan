import sys


class Progress(object):
    def __init__(self, total: int):
        self.progress: float = 0.0
        self.total = total

    def update_progress(self, progress):
        bar_length = 20
        if isinstance(progress, int):
            progress = float(progress)
        if not isinstance(progress, float):
            progress = 0
        if progress < 0:
            progress = 0
        if progress >= 1:
            progress = 1

        block = int(round(bar_length * progress))

        sys.stdout.write("\r")
        text = "Progress: [{0}] {1:.1f}%".format(
            "#" * block + "-" * (bar_length - block), progress * 100
        )
        sys.stdout.write(text)
        sys.stdout.flush()

    def increment(self):
        self.progress += 1
        self.update_progress(self.progress / self.total)

    def reset(self):
        self.progress = 0
        self.update_progress(0)

    def complete(self):
        self.progress = 1
        self.update_progress(1)
