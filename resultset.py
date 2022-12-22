from collections import defaultdict


class ResultSet:
    def __init__(self, value_type=str, xpath=None, sort=False):
        self.results_list = []
        self.results_uniq = defaultdict(list)
        self.value_type = value_type
        self.xpath = xpath

    def add(self, tag, value, lineno):
        if type(value) is not self.value_type:
            raise TypeError(
                f"{value} {type(value)} is not of type {self.value_type}"
            )
        self.results_list.append({"tag": tag, "value": value, "lineno": lineno})
        if self.value_type is str:
            self.results_uniq[value].append(lineno)
        return self

    def all_values(self):
        return self.results_list

    def values(self):
        if self.value_type is str:
            return list(self.results_uniq.keys())
        else:
            return [result["value"] for result in self.results_list]

    def join(self):
        if self.valute_type is not str:
            raise TypeError(
                f"ResultSet value type is {self.value_type} but join()"
                " expects str"
            )
        total_text = ""
        for result in self.results_list:
            total_text += " " + result["value"]
        return [total_text[1:]]

    def append(self, result_set):
        if result_set is None:
            raise TypeError(
                f"{type(result_text)} can't be appended to ResultSet"
            )
        for result in result_set.all_values():
            self.results_list.append(result)
            if self.value_type is str:
                self.results_uniq[result["value"]].append(result["lineno"])

    def isempty(self):
        return len(self.results_list) == 0

    def __str__(self):
        return "\n".join(
            [
                f"Lineno: {result['lineno']}, Tag: {result['tag']}, Value: {result['value']}"
                for result in self.results_list
            ]
        )
