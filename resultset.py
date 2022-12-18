from collections import defaultdict


class ResultSet:
    def __init__(self, value_type=str, xpath=None, sort=False):
        self.results_list = []
        self.results_uniq = defaultdict(list)
        self.value_type = value_type
        self.xpath = xpath

    def add(self, tag, value, lineno):
        if type(value) is not self.value_type:
            raise TypeError("{value} is not of type {self.value_type}")
        self.results_list.append({"tag": tag, "value": value, "lineno": lineno})
        if self.value_type is str:
            self.results_uniq[value].append(lineno)

    def values(self):
        if self.value_type is str:
            return self.results_uniq.keys()
        else:
            return [result["value"] for result in self.results_list]

    def __str__(self):
        return "\n".join(
            [
                f"Lineno: {result['lineno']}, Tag: {result['tag']}, Value: {result['value']}"
                for result in self.results_list
            ]
        )
