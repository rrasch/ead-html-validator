from collections import defaultdict


class ResultSet:
    def __init__(self, value_type=str):
        self.results_list = []
        self.results_uniq = defaultdict(list)
        self.value_type = value_type

    def add(self, tag, value, lineno):
        if type(value) is not self.value_type:
            raise TypeError("{value} is not of type {self.value_type}")
        results_list.append({"tag": tag, "value": value, "lineno": lineno})
        if self.type is str:
            results_uniq["value"].append(result["lineno"])

    def values(self):
        if self.value_type is str:
            return self.results_uniq.keys()
        else:
            return [result["value"] for result in results_list]

    def __str__(self):
        return "\n".join(
            [
                f"{result['lineno']} {result['tag']} {result['value']}"
                for result in result_list
            ]
        )
