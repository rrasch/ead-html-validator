class Errors:
    def __init__(self, exit_on_error=False):
        self.exit_on_error = exit_on_error
        self.errors = []

    def append(self, msg):
        if self.exit_on_error:
            print(msg)
            exit(1)
        else:
            self.errors.append(msg)

    def extend(self, new_errors):
        self.errors.extend(new_errors.errors)

    def __getitem__(self, index):
        return self.errors[index]

    def __setitem__(self, index, value):
        self.errors[index] = value

    def __bool__(self):
        return len(self.errors) > 0

    def __len__(self):
        return len(self.errors)

    def __iter__(self):
        self.current = 0
        return self

    def __next__(self):
        if self.current < len(self.errors):
            result = self.errors[self.current]
            self.current += 1
            return result
        else:
            raise StopIteration
