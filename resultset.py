from collections import defaultdict
import json


class ResultSetIter:
    def __init__(self):
        pass

    def __iter__(self):
        pass

    def __next__(self):
        pass


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

    def _values(self):
        if self.value_type is str:
            return list(self.results_uniq.keys())
        else:
            return [result["value"] for result in self.results_list]

    def values(self):
        if self.value_type is str:
            return list(self.results_uniq.keys())
        else:
            return [
                json.dumps(result["value"], indent=2)
                for result in self.results_list
            ]

    def type(self):
        return self.value_type

    def update_values(self, update_func):
        updated = ResultSet(value_type=self.value_type)
        for result in self.all_values():
            updated.add(
                result["tag"], update_func(result["value"]), result["lineno"]
            )
        return updated

    def join(self, uniq=True, sep=" "):
        if self.value_type is not str:
            raise TypeError(
                f"ResultSet value type is {self.value_type} but join()"
                " expects str"
            )
        if self.isempty():
            raise ValueError("ResultSet is empty.")

        if uniq:
            values = self.results_uniq.keys()
        else:
            values = [result["value"] for result in self.results_list]

        total_text = ""
        for value in values:
            if total_text:
                total_text += sep
            total_text += value

        joined = ResultSet(value_type=self.value_type)
        joined.add(
            self.results_list[0]["tag"],
            total_text,
            self.results_list[0]["lineno"],
        )
        return joined

    def append(self, result_set):
        if result_set is None:
            raise TypeError(
                f"{type(result_text)} can't be appended to ResultSet"
            )
        for result in result_set.all_values():
            self.results_list.append(result)
            if self.value_type is str:
                self.results_uniq[result["value"]].append(result["lineno"])

    def grep(self, filter_func):
        filtered = ResultSet(value_type=self.value_type)
        for result in result_set.all_values():
            if filter_func(result["value"]):
                filtered.add(result["tag"], result["value"], result["lineno"])
        return filtered if filtered else None

    def isempty(self):
        return len(self.results_list) == 0

    def __str__(self):
        return "\n\n".join(
            [
                f"Lineno: {result['lineno']}, Tag: {result['tag']}, Value:"
                f" '{result['value']}'"
                for result in self.results_list
            ]
        )

    def __bool__(self):
        return len(self.results_list) > 0

    def __iter__(self):
        for result in self.all_values():
            yield result
